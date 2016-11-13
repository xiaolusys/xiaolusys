# -*- coding:utf-8 -*-
from __future__ import absolute_import, unicode_literals
from celery import shared_task as task

import time
import datetime
import calendar
import json

from django.conf import settings
from django.db import transaction
from django.db.models import Q, Sum, Count, F
from shopback import paramconfig as pcfg
from shopback.orders.models import Trade, Order
from shopback.trades.service import TradeService
from shopback.items.models import Product, ProductSku
from shopback.trades.models import (MergeTrade,
                                    MergeBuyerTrade,
                                    ReplayPostTrade,
                                    MergeTradeDelivery)
from core.options import log_action, User as DjangoUser, ADDITION, CHANGE
from common.utils import update_model_fields
from shopback.users.models import User, Customer
import logging

logger = logging.getLogger('celery.handler')
LOGISTIC_DIR = 'logistic'
ORDER_DIR = 'order'
REPORT_DIR = 'report'
FINANCE_DIR = 'finance'


class SubTradePostException(Exception):
    def __init__(self, msg=''):
        self.message = msg

    def __str__(self):
        return self.message


def get_trade_pickle_list_data(post_trades):
    """生成配货单数据列表"""

    trade_items = {}
    for trade in post_trades:
        used_orders = trade.merge_orders.filter(sys_status=pcfg.IN_EFFECT) \
            .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE)
        for order in used_orders:
            outer_id = order.outer_id or str(order.num_iid)
            outer_sku_id = order.outer_sku_id or str(order.sku_id)

            prod = None
            prod_sku = None
            try:
                prod = Product.objects.get(outer_id=outer_id)
                prod_sku = ProductSku.objects.get(outer_id=outer_sku_id, product=prod)
            except:
                pass

            location = prod_sku and prod_sku.get_districts_code() or (prod and prod.get_districts_code() or '')
            if trade_items.has_key(outer_id):
                trade_items[outer_id]['num'] += order.num
                skus = trade_items[outer_id]['skus']
                if skus.has_key(outer_sku_id):
                    skus[outer_sku_id]['num'] += order.num
                else:
                    prod_sku_name = prod_sku.name if prod_sku else order.sku_properties_name
                    skus[outer_sku_id] = {'sku_name': prod_sku_name,
                                          'num': order.num,
                                          'location': location}
            else:
                prod_sku_name = prod_sku.properties_name if prod_sku else order.sku_properties_name

                trade_items[outer_id] = {
                    'num': order.num,
                    'title': prod.name if prod else order.title,
                    'location': prod and prod.get_districts_code() or '',
                    'skus': {outer_sku_id: {
                        'sku_name': prod_sku_name,
                        'num': order.num,
                        'location': location}}
                }

    trade_list = sorted(trade_items.items(), key=lambda d: d[1]['num'], reverse=True)
    for trade in trade_list:
        skus = trade[1]['skus']
        trade[1]['skus'] = sorted(skus.items(), key=lambda d: d[1]['num'], reverse=True)

    return trade_list


def get_replay_results(replay_trade):
    reponse_result = replay_trade.post_data
    if not reponse_result:

        trade_ids = replay_trade.trade_ids.split(',')
        queryset = MergeTrade.objects.filter(id__in=trade_ids)

        post_trades = queryset.filter(sys_status__in=(pcfg.WAIT_CHECK_BARCODE_STATUS,
                                                      pcfg.WAIT_SCAN_WEIGHT_STATUS,
                                                      pcfg.FINISHED_STATUS))
        trade_list = get_trade_pickle_list_data(post_trades)

        trades = []
        for trade in queryset:
            trade_dict = {}
            trade_dict['id'] = trade.id
            trade_dict['tid'] = trade.tid
            trade_dict['seller_nick'] = trade.user.nick
            trade_dict['buyer_nick'] = trade.buyer_nick
            trade_dict['company_name'] = (trade.logistics_company and
                                          trade.logistics_company.name or '--')
            trade_dict['out_sid'] = trade.out_sid
            trade_dict['is_success'] = trade.sys_status in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                                                            pcfg.WAIT_SCAN_WEIGHT_STATUS,
                                                            pcfg.FINISHED_STATUS)
            trade_dict['sys_status'] = trade.sys_status
            trades.append(trade_dict)

        reponse_result = {'trades': trades, 'trade_items': trade_list, 'post_no': replay_trade.id}

        replay_trade.succ_ids = ','.join([str(t.id) for t in post_trades])
        replay_trade.succ_num = post_trades.count()
        replay_trade.post_data = json.dumps(reponse_result)
        replay_trade.status = pcfg.RP_WAIT_ACCEPT_STATUS
        replay_trade.finished = datetime.datetime.now()
        replay_trade.save()
    else:
        reponse_result = json.loads(reponse_result)
    return reponse_result


def get_package_pickle_list_data(post_trades):
    """生成包裹配货单数据列表"""
    trade_items = {}
    for trade in post_trades:
        used_orders = trade.package_sku_items
        for order in used_orders:
            outer_id = order.outer_id
            outer_sku_id = order.outer_sku_id or str(order.sku_id)
            # prod = Product.objects.get(outer_id=outer_id)
            # prod_sku = ProductSku.objects.get(outer_id=outer_sku_id, product=prod)
            prod_sku = order.product_sku
            prod = order.product_sku.product
            location = prod_sku and prod_sku.get_districts_code() or (prod and prod.get_districts_code() or '')
            if trade_items.has_key(outer_id):
                trade_items[outer_id]['num'] += order.num
                skus = trade_items[outer_id]['skus']
                if skus.has_key(outer_sku_id):
                    skus[outer_sku_id]['num'] += order.num
                else:
                    prod_sku_name = prod_sku.name if prod_sku else order.sku_properties_name
                    skus[outer_sku_id] = {'sku_name': prod_sku_name,
                                          'num': order.num,
                                          'location': location}
            else:
                prod_sku_name = prod_sku.properties_name if prod_sku else order.sku_properties_name

                trade_items[outer_id] = {
                    'num': order.num,
                    'title': prod.name if prod else order.title,
                    'location': prod and prod.get_districts_code() or '',
                    'skus': {outer_sku_id: {
                        'sku_name': prod_sku_name,
                        'num': order.num,
                        'location': location}}
                }

    trade_list = sorted(trade_items.items(), key=lambda d: d[1]['num'], reverse=True)
    for trade in trade_list:
        skus = trade[1]['skus']
        trade[1]['skus'] = sorted(skus.items(), key=lambda d: d[1]['num'], reverse=True)

    return trade_list


def get_replay_package_results(replay_trade):
    reponse_result = replay_trade.post_data
    if not reponse_result:
        trade_ids = replay_trade.trade_ids.split(',')
        queryset = PackageOrder.objects.filter(pid__in=trade_ids)
        post_trades = queryset.filter(sys_status__in=(PackageOrder.WAIT_CHECK_BARCODE_STATUS,
                                                      PackageOrder.WAIT_SCAN_WEIGHT_STATUS,
                                                      PackageOrder.WAIT_CUSTOMER_RECEIVE,
                                                      PackageOrder.FINISHED_STATUS))
        trade_list = get_package_pickle_list_data(post_trades)
        trades = []
        for trade in queryset:
            trade_dict = {}
            trade_dict['id'] = trade.id
            trade_dict['tid'] = trade.tid
            trade_dict['seller_nick'] = trade.seller.nick
            trade_dict['buyer_nick'] = trade.buyer_nick
            trade_dict['company_name'] = (trade.logistics_company and
                                          trade.logistics_company.name or '--')
            trade_dict['out_sid'] = trade.out_sid
            trade_dict['is_success'] = trade.sys_status in (PackageOrder.WAIT_CHECK_BARCODE_STATUS,
                                                            PackageOrder.WAIT_SCAN_WEIGHT_STATUS,
                                                            PackageOrder.WAIT_CUSTOMER_RECEIVE,
                                                            PackageOrder.FINISHED_STATUS)
            trade_dict['sys_status'] = trade.sys_status
            trades.append(trade_dict)
        reponse_result = {'trades': trades, 'trade_items': trade_list, 'post_no': replay_trade.id}
        replay_trade.succ_ids = ','.join([str(t.id) for t in post_trades])
        replay_trade.succ_num = post_trades.count()
        replay_trade.post_data = json.dumps(reponse_result)
        replay_trade.status = pcfg.RP_WAIT_ACCEPT_STATUS
        replay_trade.finished = datetime.datetime.now()
        replay_trade.save()
    else:
        reponse_result = json.loads(reponse_result)
    return reponse_result


@task()
def sendTradeCallBack(trade_ids, *args, **kwargs):
    try:
        replay_trade = ReplayPostTrade.objects.get(id=args[0])
    except:
        return None
    else:
        try:
            get_replay_results(replay_trade)
        except Exception, exc:
            logger.error('trade post callback error:%s' % exc.message, exc_info=True)
        return None


@task()
def send_package_call_Back(trade_ids, *args, **kwargs):
    try:
        replay_trade = ReplayPostTrade.objects.get(id=args[0])
    except:
        return None
    else:
        try:
            get_replay_package_results(replay_trade)
        except Exception, exc:
            logger.error('trade post callback error:%s' % exc.message, exc_info=True)
        return None


@task(ignore_result=False)
def sendTaobaoTradeTask(operator_id, trade_id):
    """ 淘宝发货任务 """

    trade = MergeTrade.objects.get(id=trade_id)
    if (not trade.is_picking_print or
            not trade.is_express_print or not trade.out_sid
        or trade.sys_status != pcfg.WAIT_PREPARE_SEND_STATUS):
        return trade_id

    if trade.status == pcfg.WAIT_BUYER_CONFIRM_GOODS:
        trade.sys_status = pcfg.WAIT_CHECK_BARCODE_STATUS
        trade.consign_time = datetime.datetime.now()
        trade.save()
        return trade_id

    if trade.status != pcfg.WAIT_SELLER_SEND_GOODS or trade.reason_code:
        trade.sys_status = pcfg.WAIT_AUDIT_STATUS
        trade.is_picking_print = False
        trade.is_express_print = False
        trade.save()
        log_action(operator_id, trade, CHANGE, u'订单不满足发货条件')
        return trade_id

    if trade.type in (pcfg.DIRECT_TYPE, pcfg.EXCHANGE_TYPE, pcfg.REISSUE_TYPE):
        trade.sys_status = pcfg.WAIT_CHECK_BARCODE_STATUS
        trade.status = pcfg.WAIT_BUYER_CONFIRM_GOODS
        trade.consign_time = datetime.datetime.now()
        trade.save()
        return trade_id

    merge_buyer_trades = []
    # 判断是否有合单子订单
    if trade.has_merge:
        merge_buyer_trades = MergeBuyerTrade.objects.filter(main_tid=trade.id)

    for sub_buyer_trade in merge_buyer_trades:
        sub_trade = MergeTrade.objects.get(id=sub_buyer_trade.sub_tid)

        mtd, state = MergeTradeDelivery.objects.get_or_create(seller=sub_trade.user,
                                                              trade_id=sub_trade.id)
        mtd.trade_no = sub_trade.tid
        mtd.buyer_nick = sub_trade.buyer_nick
        mtd.is_parent = False
        mtd.is_sub = True
        mtd.parent_tid = trade.id
        mtd.status = MergeTradeDelivery.WAIT_DELIVERY
        mtd.save()

        sub_trade.out_sid = trade.out_sid
        sub_trade.logistics_company = trade.logistics_company
        update_model_fields(sub_trade, update_fields=['out_sid', 'logistics_company'])

    mtd, state = MergeTradeDelivery.objects.get_or_create(seller=trade.user,
                                                          trade_id=trade.id)

    mtd.trade_no = trade.tid
    mtd.buyer_nick = trade.buyer_nick
    mtd.is_parent = trade.has_merge
    mtd.is_sub = False
    mtd.parent_tid = 0
    mtd.status = MergeTradeDelivery.WAIT_DELIVERY
    mtd.save()

    trade.sys_status = pcfg.WAIT_CHECK_BARCODE_STATUS
    trade.save()
    log_action(operator_id, trade, CHANGE, u'订单打印')

    return trade_id


@task(ignore_result=False)
def send_package_task(operator_id, trade_id):
    """ 淘宝发货任务 """
    # trade = MergeTrade.objects.get(id=trade_id)
    package = PackageOrder.objects.get(pid=trade_id)
    if (not package.is_picking_print or
            not package.is_express_print or not package.out_sid
        or package.sys_status != PackageOrder.WAIT_PREPARE_SEND_STATUS):
        return trade_id

    mtd, state = MergeTradeDelivery.objects.get_or_create(seller=package.seller,
                                                          trade_id=package.pid)

    mtd.trade_no = package.tid
    mtd.buyer_nick = package.buyer_nick
    mtd.is_parent = False
    mtd.is_sub = False
    mtd.parent_tid = 0
    mtd.status = MergeTradeDelivery.WAIT_DELIVERY
    mtd.save()

    package.sys_status = PackageOrder.WAIT_CHECK_BARCODE_STATUS
    package.save()
    log_action(operator_id, package, CHANGE, u'包裹订单打印')

    return trade_id


@task(ignore_result=False)
def deliveryTradeCallBack(*args, **kwargs):
    return (None)


@task(max_retries=3, default_retry_delay=30, ignore_result=False)
def uploadTradeLogisticsTask(trade_id, operator_id):
    try:
        merge_trade = MergeTrade.objects.get(id=trade_id)
        delivery_trade = MergeTradeDelivery.objects.get(trade_id=trade_id)

        if not delivery_trade.is_sub and merge_trade.sys_status != pcfg.FINISHED_STATUS:
            delivery_trade.message = u'订单未称重'
            delivery_trade.status = MergeTradeDelivery.FAIL_DELIVERY
            delivery_trade.save()
            return

        if delivery_trade.is_sub and merge_trade.sys_status == pcfg.ON_THE_FLY_STATUS:
            main_trade = MergeTrade.objects.get(id=delivery_trade.parent_tid)
            if main_trade.sys_status != pcfg.FINISHED_STATUS:
                delivery_trade.message = u'父订单未称重'
                delivery_trade.status = MergeTradeDelivery.FAIL_DELIVERY
                delivery_trade.save()
                return

            merge_trade.logistics_company = main_trade.logistics_company
            merge_trade.out_sid = main_trade.out_sid
            merge_trade.save()

        if (delivery_trade.is_sub
            and merge_trade.sys_status in [pcfg.WAIT_AUDIT_STATUS,
                                           pcfg.WAIT_PREPARE_SEND_STATUS,
                                           pcfg.INVALID_STATUS,
                                           pcfg.REGULAR_REMAIN_STATUS]):
            delivery_trade.delete()
            return

        tservice = TradeService(merge_trade.user.visitor_id, merge_trade)
        tservice.sendTrade()

    except Exception, exc:

        merge_trade.append_reason_code(pcfg.POST_MODIFY_CODE)
        MergeTradeDelivery.objects.filter(trade_id=trade_id).update(
            status=MergeTradeDelivery.FAIL_DELIVERY,
            message=exc.message)

        log_action(operator_id, merge_trade, CHANGE, u'单号上传失败:%s' % exc.message)

    else:
        delivery_trade.delete()

        if delivery_trade.is_sub and merge_trade.sys_status == pcfg.ON_THE_FLY_STATUS:
            merge_trade.sys_status = pcfg.FINISHED_STATUS

        merge_trade.status = pcfg.WAIT_BUYER_CONFIRM_GOODS
        merge_trade.consign_time = datetime.datetime.now()
        merge_trade.save()

        log_action(operator_id, merge_trade, CHANGE,
                   u'快递单号上传成功[%s:%s]' % (merge_trade.logistics_company.name, merge_trade.out_sid))


@task()
def regularRemainOrderTask():
    """更新定时提醒订单"""
    dt = datetime.datetime.now()
    MergeTrade.objects.filter(Q(remind_time__lte=dt) | Q(remind_time=None),
                              sys_status=pcfg.REGULAR_REMAIN_STATUS) \
        .update(sys_status=pcfg.WAIT_AUDIT_STATUS)


@task
def saveTradeByTidTask(tid, seller_nick):
    user = User.objects.get(nick=seller_nick)
    Trade.get_or_create(tid, user.visitor_id)


@task()
def importTradeFromFileTask(fileName):
    """根据导入文件获取淘宝订单"""
    with open(fileName, 'r') as f:
        for line in f:
            if not line:
                continue

            try:
                seller_nick, tid = line.split(',')
                if tid:
                    saveTradeByTidTask.delay(tid, seller_nick.decode('gbk'))
            except:
                pass


@task()
def pushBuyerToCustomerTask(day):
    """ 将订单买家信息保存为客户信息 """

    dt = datetime.datetime.now()
    all_trades = MergeTrade.objects.filter(
        created__gte=dt - datetime.timedelta(day, 0, 0)).order_by('-pay_time')

    for trade in all_trades:
        try:
            if not (trade.receiver_mobile or trade.receiver_phone):
                return

            customer, state = Customer.objects.get_or_create(
                nick=trade.buyer_nick,
                mobile=trade.receiver_mobile,
                phone=trade.receiver_phone)

            customer.name = trade.receiver_name
            customer.zip = trade.receiver_zip
            customer.address = trade.receiver_address
            customer.city = trade.receiver_city
            customer.state = trade.receiver_state
            customer.district = trade.receiver_district
            customer.save()

            trades = MergeTrade.objects.filter(buyer_nick=trade.buyer_nick,
                                               receiver_mobile=trade.receiver_mobile,
                                               status__in=pcfg.ORDER_SUCCESS_STATUS) \
                .exclude(is_express_print=False,
                         sys_status=pcfg.FINISHED_STATUS).order_by('-pay_time')
            trade_num = trades.count()

            if trades.count() > 0 and trade_num != customer.buy_times:
                total_nums = trades.count()
                total_payment = trades.aggregate(total_payment=Sum('payment')).get('total_payment') or 0

                customer.last_buy_time = trades[0].pay_time
                customer.buy_times = trades.count()
                customer.avg_payment = float(round(float(total_payment) / total_nums, 2))
                customer.save()
        except:
            pass


import os
from django.db import connection, IntegrityError
from common.utils import CSVUnicodeWriter
from shopback.users.models import User
from shopback.logistics.models import LogisticsCompany


def get_User_Key_Name_Map():
    kn_maps = {}
    users = User.objects.all()
    for user in users:
        kn_maps['%s' % user.id] = user.nick

    return kn_maps


def get_Logistic_Company_Key_Name_Map():
    kn_maps = {}
    logistics = LogisticsCompany.objects.all()
    for lg in logistics:
        kn_maps['%s' % lg.id] = lg.name

    return kn_maps


from common.utils import replace_utf8mb4


@task()
def task_Gen_Order_Report_File(date_from, date_to, file_dir=None):
    un_maps = get_User_Key_Name_Map()
    lc_maps = get_Logistic_Company_Key_Name_Map()

    fields = ['tid', 'user_id', 'buyer_nick', 'payment', 'post_fee', 'pay_time', 'weight_time', 'receiver_mobile',
              'receiver_phone', 'receiver_state', 'receiver_city', 'out_sid', 'logistics_company_id', 'sys_status']
    dump_fields = ','.join(fields)
    date_from_str = date_from.strftime('%Y-%m-%d %H:%M:%S')
    date_to_str = date_to.strftime('%Y-%m-%d %H:%M:%S')
    exec_sql = "select {0} from shop_trades_mergetrade where pay_time > '{1}' and pay_time < '{2}';".format(dump_fields,
                                                                                                            date_from_str,
                                                                                                            date_to_str)

    try:
        cursor = connection.cursor()
        cursor.execute(exec_sql)
        cursor_set = cursor.fetchall()

        field_name_list = [u'原始单号', u'店铺名称', u'会员名称', u'付款金额', u'实付邮费', u'付款日期', u'称重日期', u'手机', u'电话', u'省', u'市',
                           u'运单号', u'快递名称', u'订单状态']

        if not file_dir:
            file_dir = os.path.join(settings.DOWNLOAD_ROOT, ORDER_DIR)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        file_name = u'order_%s~%s.csv' % (date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d'))
        file_path_name = os.path.join(file_dir, file_name)
        with open(file_path_name, 'w+') as myfile:

            writer = CSVUnicodeWriter(myfile, encoding='gbk')
            writer.writerow(field_name_list)

            for t in cursor_set:
                row = ['%s' % r for r in t]
                row[2] = replace_utf8mb4(row[2])
                row[1] = un_maps.get(str(t[1]), u'未找到')
                row[10] = lc_maps.get(str(t[10]), u'未找到')
                writer.writerow(row)
    finally:
        cursor.close()


@task()
def task_Gen_Logistic_Report_File(date_from, date_to, file_dir=None):
    un_maps = get_User_Key_Name_Map()
    lc_maps = get_Logistic_Company_Key_Name_Map()

    fields = ['out_sid', 'tid', 'user_id', 'receiver_name', 'receiver_state',
              'receiver_city', 'weight', 'logistics_company_id', 'post_fee', 'weight_time']
    dump_fields = ','.join(fields)
    date_from_str = date_from.strftime('%Y-%m-%d %H:%M:%S')
    date_to_str = date_to.strftime('%Y-%m-%d %H:%M:%S')
    exec_sql = "select {0} from shop_trades_mergetrade where weight_time > '{1}' and weight_time < '{2}';"
    exec_sql = exec_sql.format(dump_fields, date_from_str, date_to_str)

    try:
        cursor = connection.cursor()
        cursor.execute(exec_sql)
        cursor_set = cursor.fetchall()

        field_name_list = [u'运单ID', u'原始单号', u'店铺', u'收货人', u'省', u'市', u'重量', u'快递', u'实付邮费', u'称重日期']

        if not file_dir:
            file_dir = os.path.join(settings.DOWNLOAD_ROOT, LOGISTIC_DIR)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        file_name = u'logistic_%s~%s.csv' % (date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d'))
        file_path_name = os.path.join(file_dir, file_name)
        with open(file_path_name, 'w+') as myfile:

            writer = CSVUnicodeWriter(myfile, encoding='gbk')
            writer.writerow(field_name_list)

            for t in cursor_set:
                row = ['%s' % r for r in t]
                row[2] = un_maps.get(str(t[2]), u'未找到')
                row[7] = lc_maps.get(str(t[7]), u'未找到')
                writer.writerow(row)
    finally:
        cursor.close()


from shopback.trades.models import MergeOrder


def origin_price_payment(trade_id):
    origin_price = 0
    payment = 0
    merge_orders = MergeOrder.objects.filter(merge_trade=trade_id)
    for order in merge_orders.filter(is_merge=False,
                                     gift_type=pcfg.REAL_ORDER_GIT_TYPE) \
            .values('outer_id', 'outer_sku_id', 'payment', 'num'):
        order_origin = 0
        try:
            product = Product.objects.get(outer_id=order['outer_id'])
            psku = None
            if order['outer_sku_id']:
                psku = ProductSku.objects.get(outer_id=order['outer_sku_id'],
                                              product=product)
            order_origin = psku and psku.cost * order['num'] or product.cost * order['num']
        except (Product.DoesNotExist, ProductSku.DoesNotExist):
            pass
        origin_price += order_origin
        payment += order['payment']

    return (origin_price, payment)


def is_order_refund(status, sys_status):
    if status == pcfg.TRADE_CLOSED or sys_status == pcfg.INVALID_STATUS:
        return True
    return False


@task()
def task_Gen_XiaoluSale_Report(date_from, date_to, file_dir=''):
    un_maps = get_User_Key_Name_Map()

    fields = ['id', 'tid', 'user_id', 'receiver_mobile', 'buyer_nick', 'pay_time', 'payment', 'status', 'sys_status']
    dump_fields = ','.join(fields)
    date_from_str = date_from.strftime('%Y-%m-%d %H:%M:%S')
    date_to_str = date_to.strftime('%Y-%m-%d %H:%M:%S')
    exec_sql = (
        "select {0} from shop_trades_mergetrade where pay_time between '{1}' and '{2}' and type in ('wx','sale');"
            .format(dump_fields, date_from_str, date_to_str))

    try:
        cursor = connection.cursor()
        cursor.execute(exec_sql)
        cursor_set = cursor.fetchall()

        field_name_list = [u'订单编号', u'原单编号', u'店铺名称', u'手机号', u'买家ID', u'付款日期', u'货品价格', u'订单金额', u'是否退款']

        if not file_dir:
            file_dir = os.path.join(settings.DOWNLOAD_ROOT, REPORT_DIR)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        file_name = u'order_report_%s~%s.csv' % (date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d'))
        file_path_name = os.path.join(file_dir, file_name)
        with open(file_path_name, 'w+') as myfile:

            writer = CSVUnicodeWriter(myfile, encoding='gbk')
            writer.writerow(field_name_list)

            for t in cursor_set:
                row = []
                row.append(t[0])
                row.append(t[1])
                row.append(un_maps.get(str(t[2]), u'未找到'))
                row.append(t[3])
                row.append(replace_utf8mb4(t[4]))
                row.append(t[5])

                price_tp = origin_price_payment(t[0])
                order_refund = is_order_refund(t[7], t[8])
                row.append(price_tp[0])
                row.append(price_tp[1])
                row.append(order_refund and u'是' or u'否')
                writer.writerow(['%s' % r for r in row])
    finally:
        cursor.close()


def previous_year_month(year, month):
    if month == 1:
        return year - 1, 12
    return year, month - 1


@task()
def task_Gen_Logistic_Report_File_By_Month(pre_month=1):
    dt = datetime.datetime.now()
    year, month = dt.year, dt.month
    for i in range(0, pre_month):
        year, month = previous_year_month(year, month)

    month_range = calendar.monthrange(year, month)
    date_from = datetime.datetime(year, month, 1, 0, 0, 0)
    date_to = datetime.datetime(year, month, month_range[1], 23, 59, 59)

    task_Gen_Logistic_Report_File(date_from, date_to)


from common.utils import (parse_date, CSVUnicodeWriter, parse_datetime, format_date, format_datetime)
from shopback.refunds.models import REFUND_STATUS, Refund


@task()
def task_Gen_Product_Statistic(shop_id, sc_by, wait_send, p_outer_id, start_dt, end_dt, is_sale="1"):
    order_qs = getSourceOrders(shop_id=shop_id, sc_by=sc_by, wait_send=wait_send,
                               p_outer_id=p_outer_id, start_dt=start_dt, end_dt=end_dt, is_sale=is_sale)

    empty_order_qs = getSourceOrders(shop_id=shop_id,
                                     sc_by=sc_by,
                                     wait_send=wait_send,
                                     p_outer_id=p_outer_id,
                                     start_dt=start_dt,
                                     end_dt=end_dt,
                                     empty_code=True)

    trade_qs = getSourceTrades(order_qs)

    buyer_nums = len(trade_qs)
    trade_nums = len(trade_qs)
    total_post_fee = 0.00

    refund_fees = getTotalRefundFee(order_qs)
    empty_order_count = empty_order_qs.count()
    trade_list = getTradeSortedItems(order_qs, is_sale=is_sale)
    total_num = trade_list.pop()
    total_cost = trade_list.pop()
    total_sales = trade_list.pop()
    return {'trade_items': trade_list,
            'empty_order_count': empty_order_count,
            'total_cost': total_cost and round(total_cost, 2) or 0,
            'total_sales': total_sales and round(total_sales, 2) or 0,
            'total_num': total_num,
            'refund_fees': refund_fees and round(refund_fees, 2) or 0,
            'buyer_nums': buyer_nums,
            'trade_nums': trade_nums,
            'post_fees': total_post_fee}


def getSourceOrders(shop_id=None, is_sale=None,
                    sc_by='created', start_dt=None,
                    end_dt=None, wait_send='0',
                    p_outer_id='', empty_code=False):
    order_qs = MergeOrder.objects.filter(sys_status=pcfg.IN_EFFECT) \
        .exclude(merge_trade__type=pcfg.REISSUE_TYPE) \
        .exclude(merge_trade__type=pcfg.EXCHANGE_TYPE) \
        .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE)
    if shop_id:
        order_qs = order_qs.filter(merge_trade__user=shop_id)

    if sc_by == 'pay':
        order_qs = order_qs.filter(pay_time__gte=start_dt, pay_time__lte=end_dt)
    elif sc_by == 'weight':
        order_qs = order_qs.filter(merge_trade__weight_time__gte=start_dt,
                                   merge_trade__weight_time__lte=end_dt)
    else:
        order_qs = order_qs.filter(created__gte=start_dt, created__lte=end_dt)

    if wait_send == '1':
        order_qs = order_qs.filter(merge_trade__sys_status=pcfg.WAIT_PREPARE_SEND_STATUS)
    elif wait_send == '2':
        order_qs = order_qs.filter(merge_trade__status__in=pcfg.ORDER_SUCCESS_STATUS,
                                   merge_trade__sys_status__in=pcfg.WAIT_WEIGHT_STATUS)
    else:
        order_qs = order_qs.filter(merge_trade__status__in=pcfg.ORDER_SUCCESS_STATUS) \
            .exclude(merge_trade__sys_status__in=(pcfg.INVALID_STATUS, pcfg.ON_THE_FLY_STATUS)) \
            .exclude(merge_trade__sys_status=pcfg.FINISHED_STATUS, merge_trade__is_express_print=False)

    if empty_code:
        order_qs = order_qs.filter(outer_id='')
        return order_qs

    if is_sale:
        order_qs = order_qs.extra(where=["CHAR_LENGTH(outer_id)>=9"]) \
            .filter(Q(outer_id__startswith="9") | Q(outer_id__startswith="1") | Q(outer_id__startswith="8"))

    if p_outer_id:
        order_qs = order_qs.filter(outer_id__startswith=p_outer_id)

    return order_qs


def getSourceTrades(order_qs):
    trade_ids = [t[0] for t in order_qs.values_list('merge_trade__id')]
    return set(trade_ids)


def getTotalRefundFee(order_qs):
    effect_oids = getEffectOrdersId(order_qs)

    return Refund.objects.filter(oid__in=effect_oids, status__in=(
        pcfg.REFUND_WAIT_SELLER_AGREE, pcfg.REFUND_CONFIRM_GOODS, pcfg.REFUND_SUCCESS)) \
               .aggregate(total_refund_fee=Sum('refund_fee')).get('total_refund_fee') or 0


def getTradeSortedItems(order_qs, is_sale=False):
    trade_items = {}
    for order in order_qs:

        outer_id = order.outer_id.strip() or str(order.num_iid)
        outer_sku_id = order.outer_sku_id.strip() or str(order.sku_id)
        payment = float(order.payment or 0)
        order_num = order.num or 0
        prod, prod_sku = getProductAndSku(outer_id, outer_sku_id)

        if trade_items.has_key(outer_id):
            trade_items[outer_id]['num'] += order_num
            skus = trade_items[outer_id]['skus']

            if skus.has_key(outer_sku_id):
                skus[outer_sku_id]['num'] += order_num
                skus[outer_sku_id]['cost'] += skus[outer_sku_id]['std_purchase_price'] * order_num
                skus[outer_sku_id]['sales'] += payment
                # 累加商品成本跟销售额
                trade_items[outer_id]['cost'] += skus[outer_sku_id]['std_purchase_price'] * order_num
                trade_items[outer_id]['sales'] += payment
            else:
                prod_sku_name = prod_sku.name if prod_sku else order.sku_properties_name
                purchase_price = float(prod_sku.cost) if prod_sku else 0
                # 累加商品成本跟销售额
                trade_items[outer_id]['cost'] += purchase_price * order_num
                trade_items[outer_id]['sales'] += payment

                skus[outer_sku_id] = {
                    'sku_name': prod_sku_name,
                    'num': order_num,
                    'cost': purchase_price * order_num,
                    'sales': payment,
                    'std_purchase_price': purchase_price}
        else:
            prod_sku_name = prod_sku.name if prod_sku else order.sku_properties_name
            purchase_price = float(prod_sku.cost) if prod_sku else payment / order_num
            trade_items[outer_id] = {
                'product_id': prod and prod.id or None,
                'num': order_num,
                'title': prod.name if prod else order.title,
                'cost': purchase_price * order_num,
                'pic_path': prod and prod.PIC_PATH or '',
                'sales': payment,
                'sale_charger': prod and prod.sale_charger or '',
                'storage_charger': prod and prod.storage_charger or '',
                'sales': payment,
                'skus': {outer_sku_id: {
                    'sku_name': prod_sku_name,
                    'num': order_num,
                    'cost': purchase_price * order_num,
                    'sales': payment,
                    'std_purchase_price': purchase_price}}
            }

    if is_sale:
        def sort_items(x, y):
            if x[0][:-1] == y[0][:-1]:
                return -cmp(x[1], y[1])
            return cmp(x[0], y[0])

        order_items = sorted(trade_items.items(), key=lambda d: (d[0], d[1]['num']), cmp=sort_items)
    else:
        order_items = sorted(trade_items.items(), key=lambda d: d[1]['num'], reverse=True)

    total_cost = 0
    total_sales = 0
    total_num = 0
    for trade in order_items:
        total_cost += trade[1]['cost']
        total_sales += trade[1]['sales']
        total_num += trade[1]['num']
        trade[1]['skus'] = sorted(trade[1]['skus'].items(), key=lambda d: d[0])

    order_items.append(total_sales)
    order_items.append(total_cost)
    order_items.append(total_num)

    return order_items


def getEffectOrdersId(order_qs):
    return [o[0] for o in order_qs.values_list('oid') if len(o) > 0]


def getProductAndSku(outer_id, outer_sku_id):
    prod_map = {}
    outer_key = '-'.join((outer_id, outer_sku_id))
    if prod_map.has_key(outer_key):
        return prod_map.get(outer_key)

    prod = getProductByOuterId(outer_id)
    prod_sku = getProductSkuByOuterId(outer_id, outer_sku_id)
    prod_map[outer_key] = (prod, prod_sku)
    return (prod, prod_sku)


def getProductByOuterId(outer_id):
    try:
        return Product.objects.get(outer_id=outer_id)
    except:
        return None


def getProductSkuByOuterId(outer_id, outer_sku_id):
    try:
        return ProductSku.objects.get(outer_id=outer_sku_id, product__outer_id=outer_id)
    except:
        return None


from shopback.trades.models import PackageSkuItem, PackageOrder
from flashsale.pay.models import SaleOrder, SaleTrade, SaleRefund


@task(max_retries=3, default_retry_delay=6)
def task_packageskuitem_update_productskusalestats_num(sku_id, pay_time):
    """
    Recalculate and update skustats_num.
    """
    from shopback.items.models import SkuStock, ProductSkuSaleStats
    sale_stat = ProductSkuSaleStats.get_by_sku(sku_id)
    if not sale_stat:
        return
    if (sale_stat.sale_start_time and pay_time < sale_stat.sale_start_time) \
            or (sale_stat.sale_end_time and pay_time > sale_stat.sale_end_time):
        return
    assign_num_res = PackageSkuItem.objects.filter(sku_id=sku_id, pay_time__gte=sale_stat.sale_start_time,
                                                   pay_time__lte=sale_stat.sale_end_time). \
        values('assign_status').annotate(total=Sum('num'))
    total = sum([line['total'] for line in assign_num_res if line['assign_status'] != 3])

    if sale_stat.num != total:
        sale_stat.num = total
        sale_stat.save(update_fields=["num"])


@task()
def task_update_package_stat_num(instance):
    from shopback.trades.models import PackageStat, PackageOrder
    num = PackageStat.get_sended_package_num(instance.id)
    PackageStat.objects.filter(id=instance.id).update(num=num)


@task()
def task_set_sale_order(instance):
    instance.set_sale_order_id()


@task()
@transaction.atomic
def task_update_package_order(skuitem_id):
    instance = PackageSkuItem.objects.get(id=skuitem_id)
    sale_trade = instance.sale_trade
    if not (sale_trade.buyer_id and sale_trade.user_address_id and instance.product_sku.ware_by):
        logger.error('packagize_sku_item error: sale_trade loss some info:' + str(sale_trade.id))
        return
    package_order_id = PackageOrder.gen_new_package_id(sale_trade.buyer_id, sale_trade.user_address_id,
                                                       instance.product_sku.ware_by)
    if instance.assign_status == PackageSkuItem.ASSIGNED:
        if not instance.package_order_id:
            package_order = PackageOrder.objects.filter(id=package_order_id).first()
            if not package_order:
                PackageOrder.create(package_order_id, sale_trade, PackageOrder.WAIT_PREPARE_SEND_STATUS,
                                    instance)
            else:
                PackageSkuItem.objects.filter(id=instance.id).update(package_order_id=package_order_id,
                                                                     package_order_pid=package_order.pid)
                package_order.set_redo_sign(save_data=False)
                package_order.reset_package_address()
                package_order.reset_sku_item_num()
                package_order.save()
        else:
            package_order = PackageOrder.objects.get(id=instance.package_order_id)
            if package_order.is_sent():
                logger.error(
                    'package order already send:' + package_order.id + '|sku item' + str(instance.id) + '|' + str(
                        package_order.sys_status))
                instance.clear_order_info()
            else:
                package_order.set_redo_sign(save_data=False)
                package_order.reset_package_address()
                package_order.reset_sku_item_num()
                package_order.save()
    elif instance.assign_status == PackageSkuItem.CANCELED:
        if instance.package_order_id:
            package_order = PackageOrder.objects.get(id=instance.package_order_id)
            if not package_order.is_sent():
                if package_order.package_sku_items.filter(assign_status=PackageSkuItem.ASSIGNED).exists():
                    package_order.set_redo_sign(save_data=False)
                    package_order.reset_sku_item_num()
                    package_order.can_send_time = None
                    package_order.save()
                else:
                    package_order.reset_to_new_create()
    elif instance.assign_status == PackageSkuItem.FINISHED:
        sku_items = PackageSkuItem.objects.filter(package_order_id=instance.package_order_id)
        assign_status_set = set([p.assign_status for p in sku_items])
        if PackageSkuItem.CANCELED in assign_status_set:
            assign_status_set.remove(PackageSkuItem.CANCELED)
        if len(assign_status_set) == 0:
            PackageOrder.objects.filter(id=instance.package_order_id).update(
                sys_status=PackageOrder.PKG_NEW_CREATED)
        if len(assign_status_set) > 0 and PackageSkuItem.NOT_ASSIGNED not in \
                assign_status_set and PackageSkuItem.ASSIGN_STATUS not in assign_status_set:
            PackageOrder.objects.filter(id=instance.package_order_id).update(
                sys_status=PackageOrder.WAIT_CUSTOMER_RECEIVE)


@task()
def task_merge_trade_update_package_sku_item(merge_trade):
    if merge_trade.type == pcfg.SALE_TYPE and merge_trade.sys_status == MergeTrade.FINISHED_STATUS:
        from shopback.trades.models import PackageSkuItem
        for mo in merge_trade.normal_orders:
            if mo.sale_order_id:
                sku_item = PackageSkuItem.objects.get(sale_order_id=mo.sale_order_id)
                sku_item.assign_status = PackageSkuItem.FINISHED
                sku_item.set_assign_status_time()
                sku_item.save()


@task()
def task_merge_trade_update_sale_order(merge_trade):
    if merge_trade.type == pcfg.SALE_TYPE and merge_trade.sys_status == MergeTrade.FINISHED_STATUS:
        from shopback.trades.models import PackageSkuItem
        from flashsale.pay.models import SaleOrder
        for mo in merge_trade.normal_orders:
            if mo.sale_order_id:
                sale_order = SaleOrder.objects.get(id=mo.sale_order_id)
                if not sale_order.status >= SaleOrder.WAIT_BUYER_CONFIRM_GOODS:
                    sale_order.status = SaleOrder.WAIT_BUYER_CONFIRM_GOODS
                    sale_order.save()


from flashsale.pay.models import SaleOrderSyncLog


def create_packageskuitem_check_log(time_from, type, uni_key):
    time_to = time_from + datetime.timedelta(hours=1)
    sos = SaleOrder.objects.filter(status=SaleOrder.WAIT_SELLER_SEND_GOODS,
                                   refund_status__lte=SaleRefund.REFUND_REFUSE_BUYER, pay_time__gt=time_from,
                                   pay_time__lte=time_to)
    target_num = sos.count()
    actual_num = PackageSkuItem.objects.filter(pay_time__gt=time_from, pay_time__lte=time_to,
                                               assign_status__lt=PackageSkuItem.FINISHED).count()
    log = SaleOrderSyncLog(time_from=time_from, time_to=time_to, uni_key=uni_key, type=type, target_num=target_num,
                           actual_num=actual_num)
    if target_num == actual_num:
        log.status = SaleOrderSyncLog.COMPLETED
    log.save()


@task()
def task_saleorder_check_packageskuitem():
    type = SaleOrderSyncLog.SO_PSI
    log = SaleOrderSyncLog.objects.filter(type=type, status=SaleOrderSyncLog.COMPLETED).order_by('-time_from').first()
    if not log:
        return

    time_from = log.time_to
    now = datetime.datetime.now()
    if time_from > now - datetime.timedelta(hours=2):
        return

    uni_key = "%s|%s" % (type, time_from)
    log = SaleOrderSyncLog.objects.filter(uni_key=uni_key).first()
    if not log:
        create_packageskuitem_check_log(time_from, type, uni_key)
    elif not log.is_completed():
        time_to = log.time_to
        sos = SaleOrder.objects.filter(status=SaleOrder.WAIT_SELLER_SEND_GOODS,
                                       refund_status__lte=SaleRefund.REFUND_REFUSE_BUYER, pay_time__gt=time_from,
                                       pay_time__lte=time_to)
        deposit_count = 0
        teambuy_count = 0
        for so in sos:
            if so.is_deposit():
                deposit_count += 1
                continue
            if so.is_teambuy() and not so.teambuy_can_send():
                teambuy_count += 1
                continue
            psi = PackageSkuItem.objects.filter(oid=so.oid).exclude(assign_status=PackageSkuItem.CANCELED).first()
            if not psi:
                so.save()
        target_num = sos.count() - deposit_count - teambuy_count
        actual_num = PackageSkuItem.objects.filter(pay_time__gt=time_from, pay_time__lte=time_to,
                                                   assign_status__lt=PackageSkuItem.FINISHED).count()

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
            logger.error("task_saleorder_check_packageskuitem | uni_key: %s, target_num: %s, actual_num: %s" % (
                uni_key, target_num, actual_num))


def create_packageorder_finished_check_log(time_from, uni_key):
    """
        确保已备货的PackageSkuItem数量等于待发货PackageOrder关联的PackageSkuItem的数量，
        同时等于每个PackageOrder的sku_num等于其关联的PackageSkuItem的数量
    """
    time_to = time_from + datetime.timedelta(hours=1)
    actual_num = PackageSkuItem.objects.filter(finish_time__gt=time_from, finish_time__lte=time_to,
                                               assign_status=PackageSkuItem.FINISHED).count()
    target_num = PackageOrder.objects.filter(weight_time__gt=time_from, weight_time__lte=time_to,
                                             sys_status__in=[PackageOrder.WAIT_CUSTOMER_RECEIVE,
                                                             PackageOrder.FINISHED_STATUS]).aggregate(
        n=Sum('sku_num')).get('n', 0) or 0
    log = SaleOrderSyncLog(time_from=time_from, time_to=time_to, uni_key=uni_key,
                           type=SaleOrderSyncLog.PACKAGE_SKU_FINISH_NUM, target_num=target_num,
                           actual_num=actual_num)
    if target_num == actual_num:
        log.status = SaleOrderSyncLog.COMPLETED
    log.save()


@task()
def task_packageorder_send_check_packageorder():
    type = SaleOrderSyncLog.PACKAGE_SKU_FINISH_NUM
    log = SaleOrderSyncLog.objects.filter(type=type, status=SaleOrderSyncLog.COMPLETED).order_by('-time_from').first()
    if not log:
        return
    time_from = log.time_to
    now = datetime.datetime.now()
    if time_from > now - datetime.timedelta(hours=1):
        return

    uni_key = "%s|%s" % (type, time_from)
    log = SaleOrderSyncLog.objects.filter(uni_key=uni_key).first()
    if not log:
        create_packageorder_finished_check_log(time_from, uni_key)
        task_packageorder_send_check_packageorder.delay()


def create_shoppingcart_cnt_check_log(time_from, uni_key):
    from flashsale.pay.models import ShoppingCart
    from shopback.items.models import SkuStock
    actual_num = ShoppingCart.objects.filter(status=ShoppingCart.NORMAL, type=0).aggregate(n=Sum('num')).get('n') or 0
    target_num = SkuStock.objects.aggregate(n=Sum('shoppingcart_num')).get('n') or 0
    time_to = time_from + datetime.timedelta(hours=1)
    log = SaleOrderSyncLog(time_from=time_from, time_to=time_to, uni_key=uni_key,
                           type=SaleOrderSyncLog.SALE_ORDER_SHOPPING_CART, target_num=target_num,
                           actual_num=actual_num)
    if target_num == actual_num:
        log.status = SaleOrderSyncLog.COMPLETED
    log.save()


def create_waitingpay_cnt_check_log(time_from, uni_key):
    from shopback.items.models import SkuStock
    actual_num = SaleOrder.objects.filter(status=SaleOrder.WAIT_BUYER_PAY).aggregate(n=Sum("num")).get('n') or 0
    target_num = SkuStock.objects.aggregate(n=Sum('waitingpay_num')).get('n') or 0
    time_to = time_from + datetime.timedelta(hours=1)
    log = SaleOrderSyncLog(time_from=time_from, time_to=time_to, uni_key=uni_key,
                           type=SaleOrderSyncLog.SALE_ORDER_WAITING_PAY, target_num=target_num,
                           actual_num=actual_num)
    if target_num == actual_num:
        log.status = SaleOrderSyncLog.COMPLETED
    log.save()


def create_assign_check_log(time_from, uni_key):
    from shopback.items.models import SkuStock
    actual_num = PackageSkuItem.objects.filter(assign_status=1).aggregate(n=Sum('num')).get('n') or 0
    target_num = SkuStock.objects.aggregate(n=Sum('assign_num')).get('n') or 0
    time_to = time_from + datetime.timedelta(hours=1)
    log = SaleOrderSyncLog(time_from=time_from, time_to=time_to, uni_key=uni_key,
                           type=SaleOrderSyncLog.PACKAGE_ASSIGN_NUM, target_num=target_num,
                           actual_num=actual_num)
    if target_num == actual_num:
        log.status = SaleOrderSyncLog.COMPLETED
    log.save()


def create_stock_not_assign_check_log(time_from, uni_key):
    from shopback.items.models import SkuStock
    stock_not_assign_num = SkuStock.objects.filter(
        assign_num__gt=F('history_quantity') + F('inbound_quantity') + F(
            'adjust_quantity') + F('return_quantity') - F('post_num') - F(
            'rg_quantity')).count()
    empty_package_count = 0
    for p in PackageOrder.objects.filter(
            sys_status__in=[PackageOrder.WAIT_PREPARE_SEND_STATUS, PackageOrder.WAIT_CHECK_BARCODE_STATUS,
                            PackageOrder.WAIT_SCAN_WEIGHT_STATUS]):
        if p.package_sku_items.filter(
                assign_status__in=[PackageSkuItem.ASSIGNED, PackageSkuItem.VIRTUAL_ASSIGNED]).count() == 0:
            empty_package_count += 1
    # actual_num = SkuStock.objects.filter(assign_num__gt=0,
    #                                             post_num__lt=F('history_quantity') + F('inbound_quantity') + F(
    #                                                 'adjust_quantity') + F('return_quantity') - F(
    #                                                 'rg_quantity')).aggregate(n=Sum('history_quantity') + Sum('inbound_quantity') + Sum(
    #                                                 'adjust_quantity') + Sum('return_quantity') - Sum(
    #                                                 'rg_quantity')).get('n', 0)
    # sku_ids = [item['sku_id'] for item in PackageSkuItem.objects.filter(assign_status=1).values('sku_id').distinct()]
    # SkuStock.objects.filter(id__in=sku_ids).aggregate(n=Sum('history_quantity') + Sum('inbound_quantity') + Sum(
    #                                                 'adjust_quantity') + Sum('return_quantity') - Sum(
    #                                                 'rg_quantity')).get('n', 0)
    # time_to = time_from + datetime.timedelta(hours=1)
    time_to = datetime.datetime.now()
    log = SaleOrderSyncLog(time_from=time_from, time_to=time_to, uni_key=uni_key,
                           type=SaleOrderSyncLog.PACKAGE_STOCK_NOTASSIGN, target_num=stock_not_assign_num,
                           actual_num=empty_package_count)
    if stock_not_assign_num == empty_package_count == 0:
        log.status = SaleOrderSyncLog.COMPLETED
    log.save()


def create_packageorder_realtime_check_log(time_from, uni_key):
    """
        确保已备货的PackageSkuItem数量等于待发货PackageOrder关联的PackageSkuItem的数量，
        同时等于每个PackageOrder的sku_num等于其关联的PackageSkuItem的数量
    """
    target_num = PackageSkuItem.objects.filter(assign_status=1).count()
    sku_item_total = PackageOrder.objects.filter(sys_status__in=[PackageOrder.WAIT_PREPARE_SEND_STATUS,
                                                                 PackageOrder.WAIT_CHECK_BARCODE_STATUS,
                                                                 PackageOrder.WAIT_SCAN_WEIGHT_STATUS]).aggregate(
        n=Sum('sku_num')).get('n', 0) or 0
    actual_num = sum(
        [p.package_sku_items.filter(assign_status=PackageSkuItem.ASSIGNED).count() for p in PackageOrder.objects.filter(
            sys_status__in=[PackageOrder.WAIT_PREPARE_SEND_STATUS, PackageOrder.WAIT_CHECK_BARCODE_STATUS,
                            PackageOrder.WAIT_SCAN_WEIGHT_STATUS])])
    actual_num = min(sku_item_total, actual_num)
    log = SaleOrderSyncLog(time_from=time_from, time_to=datetime.datetime.now(), uni_key=uni_key,
                           type=SaleOrderSyncLog.PACKAGE_SKU_NUM, target_num=target_num,
                           actual_num=actual_num)
    if target_num == actual_num:
        log.status = SaleOrderSyncLog.COMPLETED
    log.save()


@task()
def task_schedule_check_packageskuitem_cnt():
    realtime_check(SaleOrderSyncLog.PACKAGE_SKU_NUM, create_packageorder_realtime_check_log)


@task()
def task_schedule_check_assign_num():
    realtime_check(SaleOrderSyncLog.PACKAGE_ASSIGN_NUM, create_assign_check_log)


@task()
def task_schedule_check_stock_not_assign():
    realtime_check(SaleOrderSyncLog.PACKAGE_STOCK_NOTASSIGN, create_stock_not_assign_check_log)


@task()
def task_schedule_check_waitingpay_cnt():
    realtime_check(SaleOrderSyncLog.SALE_ORDER_WAITING_PAY, create_waitingpay_cnt_check_log)


@task()
def task_schedule_check_shoppingcart_cnt():
    realtime_check(SaleOrderSyncLog.SALE_ORDER_SHOPPING_CART, create_shoppingcart_cnt_check_log)


def realtime_check(type, func):
    log = SaleOrderSyncLog.objects.filter(type=type, status=SaleOrderSyncLog.COMPLETED).order_by('-time_from').first()
    if not log:
        return
    now = datetime.datetime.now()
    time_from = datetime.datetime(now.year, now.month, now.day, now.hour)
    if time_from <= log.time_to:
        return  # celery schedule中每半小时启动一次
    uni_key = "%s|%s" % (type, time_from)
    func(time_from, uni_key)
