# -*- coding:utf-8 -*-
from __future__ import division

__author__ = 'yann'

from celery.task import task
import datetime
import re
import sys
import urllib2
from django.db import connection
from django.db.models import Max, Sum


import common.constants
from core.options import log_action, ADDITION, CHANGE
from flashsale.dinghuo.models import OrderDetail, OrderList
from flashsale.dinghuo.models_stats import SupplyChainDataStats, PayToPackStats
from flashsale.pay.models import SaleOrder

from shopback import paramconfig as pcfg
from shopback.items.models import Product, ProductSku
from shopback.trades.models import (MergeOrder, TRADE_TYPE, SYS_TRADE_STATUS)
from supplychain.supplier.models import SaleProduct, SupplierCharge, SaleSupplier

from flashsale.dinghuo.models_purchase import PurchaseRecord, PurchaseArrangement, PurchaseDetail, PurchaseOrder
from . import utils

import logging

logger = logging.getLogger(__name__)

    

    
@task()
def task_packageskuitem_update_purchaserecord(psi):
    #print "debug: %s" % utils.get_cur_info()

    # The following code holds till all old-fashion orderdetails finish.
    #if psi.is_booking_needed():
    #    ods = OrderDetail.objects.filter(chichu_id=psi.sku_id).order_by('-created')
    #    for od in ods:
    #        if od and od.orderlist and od.orderlist.status:
    #            status = od.orderlist.status
    #            if status != OrderList.SUBMITTING and status != OrderList.ZUOFEI:
    #                if od.created > psi.pay_time:
    #                    return
    #                else:
    #                    break

    uni_key = utils.gen_purchase_record_unikey(psi)
    pr = PurchaseRecord.objects.filter(uni_key=uni_key).first()
    
    status = PurchaseRecord.EFFECT
    note = None
    if psi.is_booking_needed():
        status = PurchaseRecord.EFFECT
    elif psi.is_booking_assigned():
        status = PurchaseRecord.CANCEL
        # Read in detail the following code logic: how we judge the PSI was assigned
        # by exisiting inventory, or newly created inventory by refundproduct.
        if not pr or pr.status == PurchaseRecord.EFFECT:
            rp = RefundProduct.objects.filter(sku_id=psi.sku_id,can_reuse=True).order_by('-created').first()
            od = OrderDetail.objects.filter(chichu_id=psi.sku_id,arrival_quantity__gt=0).order_by('-arrival_time').first()

            init_time = datetime.datetime(1900,1,1)
            rp_time, od_time = init_time, init_time
            if rp:
                rp_time = rp.created
            if od and od.arrival_time:
                od_time = od.arrival_time

            if od and od.purchase_detail_unikey and od_time > psi.pay_time and od_time > rp_time:
                # In this case, the PSI was assigned by orderdetail inventory
                status = PurchaseRecord.EFFECT
            else:
                # The PSI was assigned by existing inventory or refundproduct (which increased inventory)
                note = '%s:Exist/Refund Inventory|rp:%s,od:%s' % (datetime.datetime.now(), rp_time, od_time)
    else:
        status = PurchaseRecord.CANCEL
    
    if not pr:
        fields = ['oid', 'outer_id', 'outer_sku_id', 'sku_id', 'title', 'sku_properties_name']
        pr = PurchaseRecord(package_sku_item_id=psi.id,uni_key=uni_key,request_num=psi.num,status=status)
        utils.copy_fields(pr, psi, fields)
        pr.save()
    else:
        if pr.status != status:
            update_fields = ['status', 'modified']
            pr.status = status
            if note:
                pr.note = note
                update_fields.append('note')
            pr.save(update_fields=update_fields)


@task()
def task_purchasearrangement_update_purchaserecord_book_num(pa):
    #print "debug: %s" % utils.get_cur_info()
    
    res = PurchaseArrangement.objects.filter(
        purchase_record_unikey=pa.purchase_record_unikey,
        purchase_order_status=PurchaseOrder.OPEN,
        status=PurchaseRecord.EFFECT).aggregate(total=Sum('num'))
    
    open_book_num = res['total'] or 0

    res = PurchaseArrangement.objects.filter(
        purchase_record_unikey=pa.purchase_record_unikey,
        purchase_order_status=PurchaseOrder.BOOKED).aggregate(total=Sum('num'))

    booked_num = res['total'] or 0

    book_num = open_book_num + booked_num
    

    pr = PurchaseRecord.objects.filter(uni_key=pa.purchase_record_unikey).first()
    if pr and pr.book_num != book_num:
        pr.book_num = book_num
        pr.save(update_fields=['book_num','modified'])

@task()
def task_purchase_detail_update_purchase_order(pd):
    #print "debug: %s" % utils.get_cur_info()
    res = PurchaseDetail.objects.filter(purchase_order_unikey=pd.purchase_order_unikey).\
          aggregate(b_num=Sum('book_num'),n_num=Sum('need_num'),a_num=Sum('arrival_num'))
    book_num = res['b_num'] or 0
    need_num = res['n_num'] or 0
    arrival_num = res['a_num'] or 0

    po = PurchaseOrder.objects.filter(uni_key=pd.purchase_order_unikey).first()
    if not po:
        supplier = utils.get_supplier(pd.sku_id)
        if not supplier:
            logger.error("supplier does not exist|sku_id:%s" % pd.sku_id)
            return
        po = PurchaseOrder(uni_key=pd.purchase_order_unikey,supplier_id=supplier.id,supplier_name=supplier.supplier_name,
                           book_num=book_num,need_num=need_num,arrival_num=arrival_num)
        po.save()
    else:
        if po.book_num != book_num or po.need_num != need_num or po.arrival_num != arrival_num:
            po.book_num = book_num
            po.need_num = need_num
            po.arrival_num = arrival_num
            po.save(update_fields=['book_num', 'need_num', 'arrival_num', 'modified'])


@task()
def task_purchasedetail_update_orderdetail(pd):
    # we should re-calculate the num of records each time we sync pd and od.
    res = PurchaseArrangement.objects.filter(purchase_order_unikey=pd.purchase_order_unikey,
                                             sku_id=pd.sku_id, status=PurchaseRecord.EFFECT).aggregate(total=Sum('num'))
    total = res['total'] or 0
    total_price = total * pd.unit_price_display
    
    od = OrderDetail.objects.filter(purchase_detail_unikey=pd.uni_key).first()
    if not od:
        product = utils.get_product(pd.sku_id)
        od = OrderDetail(product_id=product.id,outer_id=pd.outer_id,product_name=pd.title,chichu_id=pd.sku_id,product_chicun=pd.sku_properties_name,buy_quantity=total,buy_unitprice=pd.unit_price_display,total_price=total_price,purchase_detail_unikey=pd.uni_key,purchase_order_unikey=pd.purchase_order_unikey)
        
        ol = OrderList.objects.filter(purchase_order_unikey=pd.purchase_order_unikey).first()
        if ol:
            od.orderlist_id = ol.id
            
        od.save()
    else:
        if od.total_price != total_price or od.buy_quantity != total:
            od.buy_quantity = total
            od.buy_unitprice = pd.unit_price_display
            od.total_price = total_price
            od.save(update_fields=['buy_quantity', 'buy_unitprice', 'total_price', 'updated'])

@task()
def task_orderlist_update_self(ol):
    ol.update_stage()

@task()
def task_orderdetail_update_orderlist(od):
    if not od.purchase_order_unikey:
        od.orderlist.save()
        return
    
    ol = OrderList.objects.filter(purchase_order_unikey=od.purchase_order_unikey).first()
    if not ol:
        supplier = utils.get_supplier(od.chichu_id)
        if not supplier:
            logger.error("No supplier for orderdetail: %d" % od.id)
            return
            
        p_district = OrderList.NEAR
        if supplier.ware_by == SaleSupplier.WARE_GZ:
            p_district = OrderList.GUANGDONG
        now = datetime.datetime.now()
        ol = OrderList(purchase_order_unikey=od.purchase_order_unikey,order_amount=od.total_price,supplier_id=supplier.id,p_district=p_district,created_by=OrderList.CREATED_BY_MACHINE,status=OrderList.SUBMITTING,note=u'-->%s:动态生成订货单' % now.strftime('%m月%d %H:%M'))
        
        prev_orderlist = OrderList.objects.filter(supplier_id=supplier.id,created_by=OrderList.CREATED_BY_MACHINE).exclude(status=OrderList.ZUOFEI).order_by('-created').first()
        if prev_orderlist and prev_orderlist.buyer_id:
            ol.buyer_id = prev_orderlist.buyer_id

        ol.save()
    else:
        od_sum = OrderDetail.objects.filter(purchase_order_unikey=od.purchase_order_unikey).aggregate(total=Sum('total_price'))
        purchase_total_num = OrderDetail.objects.filter(purchase_order_unikey=od.purchase_order_unikey).count()
        total = od_sum['total'] or 0
        if ol.order_amount != total or ol.purchase_total_num != purchase_total_num:
            if ol.is_open():
                ol.order_amount = total
                ol.purchase_total_num = purchase_total_num
                ol.save(update_fields=['order_amount', 'updated', 'purchase_total_num'])
            else:
                logger.warn("ZIFEI error: tying to modify booked order_list| ol.id: %s, od: %s" % (ol.id, od.id))
        else:
            ol.save(update_fields=['updated'])

@task()
def task_purchasearrangement_update_purchasedetail(pa):
    #print "debug: %s" % utils.get_cur_info()
    
    res = PurchaseArrangement.objects.filter(purchase_order_unikey=pa.purchase_order_unikey,
                                            sku_id=pa.sku_id, status=PurchaseRecord.EFFECT).aggregate(total=Sum('num'))

    total = res['total'] or 0

    unit_price = int(utils.get_unit_price(pa.sku_id) * 100)
    uni_key = utils.gen_purchase_detail_unikey(pa)
    pd = PurchaseDetail.objects.filter(uni_key=uni_key).first()
    if not pd:
        pd = PurchaseDetail(uni_key=uni_key, purchase_order_unikey=pa.purchase_order_unikey, unit_price=unit_price,book_num=total,need_num=total)
        fields = ['outer_id', 'outer_sku_id', 'sku_id', 'title', 'sku_properties_name']
        utils.copy_fields(pd, pa, fields)
        pd.save()
    else:
        if pd.is_open():
            if pd.book_num != total or pd.unit_price != unit_price:
                pd.book_num = total
                pd.need_num = total
                pd.unit_price = unit_price
                pd.save(update_fields=['book_num','need_num', 'unit_price', 'modified'])
            return
        elif pd.is_booked():
            if pd.need_num != total or pd.unit_price != unit_price:
                pd.need_num = total
                pd.extra_num = pd.book_num - pd.need_num
                pd.unit_price = unit_price
                pd.save(update_fields=['need_num', 'extra_num', 'unit_price', 'modified'])

@task()
def task_start_booking(pr):
    #print "debug: %s" % utils.get_cur_info()

    if not pr.need_booking():
        return

    pd = PurchaseDetail.objects.filter(sku_id=pr.sku_id, extra_num__gte=pr.need_num, status=PurchaseOrder.BOOKED).first()
    if pd:
        purchase_order_unikey = pd.purchase_order_unikey
    else:
        # 2. create new purchase order
        purchase_order_unikey = utils.gen_purchase_order_unikey(pr)

    uni_key = utils.gen_purchase_arrangement_unikey(purchase_order_unikey, pr.uni_key)

    pa = PurchaseArrangement.objects.filter(uni_key=uni_key).first()
    if not pa:
        fields = ['package_sku_item_id', 'oid', 'outer_id', 'outer_sku_id', 'sku_id', 'title', 'sku_properties_name']
        pa = PurchaseArrangement(uni_key=uni_key, purchase_order_unikey=purchase_order_unikey, purchase_record_unikey=pr.uni_key, num=pr.need_num)
        utils.copy_fields(pa, pr, fields)
        pa.save()
    else:
        # We have to note that logically pa wont be an old-canceled record.
        pa.num = pa.num + pr.need_num
        pa.save(update_fields=['num', 'modified'])
    

@task()
def task_purchaserecord_adjust_purchasearrangement_overbooking(pr):
    #print "debug: %s" % utils.get_cur_info()
    
    if not pr.is_overbooked():
        return
    
    pa = PurchaseArrangement.objects.filter(sku_id=pr.sku_id, purchase_order_status=PurchaseOrder.OPEN, status=PurchaseRecord.EFFECT).first()
    if not pa:
        logger.error("severe logical error: overbooking|sku_id:%s, package_sku_item_id:%s, oid:%s, request_num:%s, book_num:%s" %
                     (pr.sku_id, pr.package_sku_item_id, pr.oid, pr.request_num, pr.book_num))
    else:
        num = min(pr.book_num - pr.request_num, pa.num)
        pa.num = pa.num - num
        pa.save(update_fields=['num', 'modified'])

    
@task()
def task_purchaserecord_sync_purchasearrangement_status(pr):
    #print "debug: %s" % utils.get_cur_info()
    
    if not pr.is_booked():
        return

    records = PurchaseArrangement.objects.filter(purchase_record_unikey=pr.uni_key)
    for record in records:
        if record.status != pr.status:
            record.status = pr.status
            record.save(update_fields=['status', 'modified'])
    

@task()
def task_check_arrangement(pd):
    #print "debug: %s" % utils.get_cur_info()
    
    if not pd.has_extra():
        return

    pa = PurchaseArrangement.objects.filter(sku_id=pd.sku_id, status=PurchaseRecord.EFFECT,purchase_order_status=PurchaseOrder.OPEN,num__gt=0).first()
    if pa:
        num = min(pd.extra_num, pa.num)
        pa.num = pa.num - num
        pa.save()


from shopapp.smsmgr.models import SMSPlatform, SMS_NOTIFY_VERIFY_CODE
from shopapp.smsmgr.service import SMS_CODE_MANAGER_TUPLE

def send_msg(mobile, content):
    platform = SMSPlatform.objects.filter(is_default=True).order_by('-id').first()
    if not platform:
        logger.error(u"send_msg: SMSPlatform object not found !")
        return
    try:
        params = {
            'content': content,
            'userid': platform.user_id,
            'account': platform.account,
            'password': platform.password,
            'mobile': mobile,
            'taskName': "小鹿美美验证码",
            'mobilenumber': 1,
            'countnumber': 1,
            'telephonenumber': 0,
            'action': 'send',
            'checkcontent': '0'
        }

        sms_manager = dict(SMS_CODE_MANAGER_TUPLE).get(platform.code, None)
        if not sms_manager:
            raise Exception('未找到短信服务商接口实现')

        manager = sms_manager()
        success = False

        # 创建一条短信发送记录
        sms_record = manager.create_record(params['mobile'], params['taskName'], SMS_NOTIFY_VERIFY_CODE,
                                           params['content'])
        # 发送短信接口
        try:
            success, task_id, succnums, response = manager.batch_send(**params)
        except Exception, exc:
            sms_record.status = pcfg.SMS_ERROR
            sms_record.memo = exc.message
            logger.error(exc.message, exc_info=True)
        else:
            sms_record.task_id = task_id
            sms_record.succnums = succnums
            sms_record.retmsg = response
            sms_record.status = success and pcfg.SMS_COMMIT or pcfg.SMS_ERROR
        sms_record.save()
        if success:
            SMSPlatform.objects.filter(code=platform.code).update(sendnums=F('sendnums') + int(succnums))
    except Exception, exc:
        logger.error(exc.message or 'empty error', exc_info=True)


@task()
def task_update_purchasedetail_status(po):
    """
    invoke when user click button to book purchase_order.
    """
    pds = PurchaseDetail.objects.filter(purchase_order_unikey=po.uni_key).update(status=po.status)

@task()
def task_update_purchasearrangement_status(po):
    """
    invoke when user click button to book purchase_order.
    """
    pas = PurchaseArrangement.objects.filter(purchase_order_unikey=po.uni_key, status=PurchaseRecord.EFFECT).update(purchase_order_status=po.status)

@task()
def task_update_purchasearrangement_initial_book(po):
    """
    invoke when user click button to book purchase_order.
    """
    pas = PurchaseArrangement.objects.filter(purchase_order_unikey=po.uni_key, status=PurchaseRecord.EFFECT)
    pas.update(purchase_order_status=po.status, initial_book=True)
    
    from shopback.trades.models import PackageSkuItem
    book_time = datetime.datetime.now()
    for pa in pas:
        psi = PackageSkuItem.objects.filter(oid=pa.oid).first()
        PackageSkuItem.objects.filter(oid=pa.oid).update(purchase_order_unikey=po.uni_key,book_time=book_time)

@task()
def task_check_with_purchase_order(ol):
    res = OrderDetail.objects.filter(orderlist=ol).aggregate(total=Sum('buy_quantity'))
    total = res['total'] or 0

    mobile = '18616787808'
    
    if not ol.supplier:
        content = 'no supplier, order_list id: %s' % ol.id
        send_msg(mobile, content)
        return
    
    supplier_id = ol.supplier.id
    po = PurchaseOrder.objects.filter(supplier_id=supplier_id).order_by('-created').first()

    if not po:
        content = 'supplier_id:%s, no book_num, %s' % (supplier_id, total)
        send_msg(mobile, content)
        return

    if po.book_num != total:
        content = 'supplier_id:%s, book_num:%s-%s' % (supplier_id, po.book_num, total)
        send_msg(mobile, content)
    
    po.status = PurchaseOrder.BOOKED
    po.save()

    task_update_purchasearrangement_status.delay(po)
    task_update_purchasearrangement_initial_book.delay(po)


from flashsale.pay.models import SaleOrderSyncLog
from shopback.trades.models import PackageSkuItem
from flashsale.dinghuo.models_purchase import PurchaseRecord

def create_purchaserecord_check_log(time_from, type, uni_key):
    psi_unikey = "%s|%s" % (SaleOrderSyncLog.SO_PSI, time_from)
    psi_log = SaleOrderSyncLog.objects.filter(uni_key=psi_unikey).first()
    if not psi_log.is_completed():
        return
    time_to = time_from + datetime.timedelta(hours=1)
    psis = PackageSkuItem.objects.filter(pay_time__gt=time_from,pay_time__lte=time_to)
    target_num = psis.count()
    actual_num = 0
    for psi in psis:
        pr = PurchaseRecord.objects.filter(oid=psi.oid).first()
        if pr:
            actual_num += 1
        elif psi.is_booking_needed():
            psi.save()
    log = SaleOrderSyncLog(time_from=time_from,time_to=time_to,uni_key=uni_key,type=type,target_num=target_num,actual_num=actual_num)
    if target_num == actual_num:
        log.status = SaleOrderSyncLog.COMPLETED
    log.save()

    
@task()
def task_packageskuitem_check_purchaserecord():
    type = SaleOrderSyncLog.PSI_PR
    log = SaleOrderSyncLog.objects.filter(type=type,status=SaleOrderSyncLog.COMPLETED).order_by('-time_from').first()
    if not log:
        return

    time_from = log.time_to
    now = datetime.datetime.now()
    
    if time_from > now - datetime.timedelta(hours=2):
        return

    uni_key = "%s|%s" % (type, time_from)
    log = SaleOrderSyncLog.objects.filter(uni_key=uni_key).first()
    if not log:
        create_purchaserecord_check_log(time_from, type, uni_key)
    elif not log.is_completed():
        time_to = log.time_to
        psis = PackageSkuItem.objects.filter(pay_time__gt=time_from,pay_time__lte=time_to)
        target_num = psis.count()
        actual_num = 0
        for psi in psis:
            pr = PurchaseRecord.objects.filter(oid=psi.oid).first()
            if pr:
                actual_num += 1
            elif psi.is_booking_needed():
                psi.save()

        update_fields = []
        if log.target_num != target_num:
            log.target_num = target_num
            update_fields.append('target_num')
        if log.actual_num != actual_num:
            log.actual_num = actual_num
            update_fields.append('actual_num')
        if target_num == actual_num:
            log.status = SaleOrderSyncLog.COMPLETED
            update_fields.append('status')
        if update_fields:
            log.save(update_fields=update_fields)
        
        if target_num != actual_num:
            logger.error("task_packageskuitem_check_purchaserecord|uni_key: %s, target_num: %s, actual_num: %s" % (uni_key, target_num, actual_num))


