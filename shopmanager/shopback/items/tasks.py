# -*- coding:utf-8 -*-
import datetime
import time
import json
from celery import Task
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.db.models import Sum, Max
from django.db import transaction
from django.db.models.query import QuerySet
from django.contrib.admin.models import CHANGE

from shopback import paramconfig as pcfg
from shopback.items.models import Item, Product, ProductSku, SkuProperty, \
    ItemNumTaskLog, ProductDaySale, ProductSkuStats, InferiorSkuStats
from shopback.fenxiao.models import FenxiaoProduct
from shopback.orders.models import Order, Trade
from shopback.trades.models import MergeOrder, MergeTrade, Refund
from shopback.users import Seller
from shopback.fenxiao.tasks import saveUserFenxiaoProductTask
from shopback import paramconfig as pcfg
from flashsale.pay.models import ModelProduct
from auth import apis
from common.utils import format_datetime, parse_datetime, get_yesterday_interval_time
from core.options import get_systemoa_user, log_action

import logging

logger = logging.getLogger(__name__)

PURCHASE_STOCK_PERCENT = 0.5
UPDATE_WAIT_POST_DAYS = 20


@task()
def updateUserItemsTask(user_id):
    """ 更新淘宝线上商品信息入库 """
    has_next = True
    cur_page = 1
    onsale_item_ids = []
    # 更新出售中的商品
    try:
        while has_next:
            response_list = apis.taobao_items_onsale_get(page_no=cur_page, tb_user_id=user_id
                                                         , page_size=settings.TAOBAO_PAGE_SIZE,
                                                         fields='num_iid,modified')
            item_list = response_list['items_onsale_get_response']
            if item_list['total_results'] > 0:
                items = item_list['items']['item']
                for item in items:
                    modified = parse_datetime(item['modified']) if item.get('modified', None) else None
                    item_obj, state = Item.objects.get_or_create(num_iid=item['num_iid'])
                    if modified != item_obj.modified:
                        response = apis.taobao_item_get(num_iid=item['num_iid'], tb_user_id=user_id)
                        item_dict = response['item_get_response']['item']
                        Item.save_item_through_dict(user_id, item_dict)
                    onsale_item_ids.append(item['num_iid'])

            total_nums = item_list['total_results']
            cur_nums = cur_page * settings.TAOBAO_PAGE_SIZE
            has_next = cur_nums < total_nums
            cur_page += 1

        # 更新库存中的商品
        has_next = True
        cur_page = 1
        while has_next:

            response_list = apis.taobao_items_inventory_get(page_no=cur_page, tb_user_id=user_id
                                                            , page_size=settings.TAOBAO_PAGE_SIZE,
                                                            fields='num_iid,modified')

            item_list = response_list['items_inventory_get_response']
            if item_list['total_results'] > 0:
                items = item_list['items']['item']
                for item in item_list['items']['item']:
                    modified = parse_datetime(item['modified']) if item.get('modified', None) else None
                    item_obj, state = Item.objects.get_or_create(num_iid=item['num_iid'])
                    if modified != item_obj.modified:
                        response = apis.taobao_item_get(num_iid=item['num_iid'], tb_user_id=user_id)
                        item_dict = response['item_get_response']['item']
                        Item.save_item_through_dict(user_id, item_dict)
                    onsale_item_ids.append(item['num_iid'])

            total_nums = item_list['total_results']
            cur_nums = cur_page * settings.TAOBAO_PAGE_SIZE
            has_next = cur_nums < total_nums
            cur_page += 1
    except:
        logger.error('update user inventory items task error', exc_info=True)
    else:
        Item.objects.filter(user__visitor_id=user_id).exclude(num_iid__in=onsale_item_ids) \
            .update(approve_status=pcfg.INSTOCK_STATUS, status=False)

    return len(onsale_item_ids)


@task()
def updateAllUserItemsTask():
    """ 更新所有用户商品信息任务 """

    users = Seller.effect_users.all()
    for user in users:
        subtask(updateUserItemsTask).delay(user.visitor_id)


@task()
def updateUserProductSkuTask(user_id=None, outer_ids=None, force_update_num=False):
    """ 更新用户商品SKU规格信息任务 """

    user = Seller.getSellerByVisitorId(user_id)
    items = user.items.filter(status=pcfg.NORMAL)
    if outer_ids:
        items = items.filter(outer_id__in=outer_ids)

    num_iids = []
    prop_dict = {}
    for index, item in enumerate(items):
        num_iids.append(item.num_iid)
        prop_dict[int(item.num_iid)] = item.property_alias_dict

        if len(num_iids) >= 40 or index + 1 == len(items):
            sku_dict = {}
            try:
                num_iids_str = ','.join(num_iids)
                response = apis.taobao_item_skus_get(num_iids=num_iids_str, tb_user_id=user_id)
                if response['item_skus_get_response'].has_key('skus'):
                    skus = response['item_skus_get_response']['skus']

                    for sku in skus.get('sku'):

                        if sku_dict.has_key(sku['num_iid']):
                            sku_dict[sku['num_iid']].append(sku)
                        else:
                            sku_dict[sku['num_iid']] = [sku]

                        item = Item.objects.get(num_iid=sku['num_iid'])

                        sku_property = SkuProperty.save_or_update(sku.copy())
                        sku_outer_id = sku.get('outer_id', '').strip()

                        if (not item.user.is_primary or not item.product
                            or item.approve_status != pcfg.ONSALE_STATUS or
                                not sku_outer_id or sku['status'] != pcfg.NORMAL):
                            continue
                        sku_prop_dict = dict([('%s:%s' % (p.split(':')[0], p.split(':')[1]),
                                               p.split(':')[3])
                                              for p in sku['properties_name'].split(';') if p])

                        pskus = ProductSku.objects.filter(outer_id=sku_outer_id,
                                                          product=item.product)
                        if pskus.count() <= 0:
                            continue

                        psku = pskus[0]
                        psku.properties_name = psku.properties_name or sku['properties_name']
                        if force_update_num:
                            wait_post_num = psku.wait_post_num >= 0 and psku.wait_post_num or 0
                            psku.quantity = sku['quantity'] + wait_post_num

                        # psku.std_sale_price =  float(sku['price'])
                        properties = ''
                        props = sku['properties'].split(';')
                        for prop in props:
                            if prop:
                                properties += (prop_dict[sku['num_iid']].get(prop, '')
                                               or sku_prop_dict.get(prop, ''))
                                psku.properties_name = properties
                                #                         psku.status = pcfg.NORMAL
                        psku.save()

            except Exception, exc:
                logger.error('update product sku error!', exc_info=True)
            finally:
                for num_iid, sku_list in sku_dict.items():
                    item = Item.objects.get(num_iid=num_iid)
                    item.skus = sku_list and json.dumps({'sku': sku_list}) or item.skus
                    item.save()

                    sku_ids = [sku['sku_id'] for sku in sku_list if sku]
                    if sku_ids:
                        SkuProperty.objects.filter(num_iid=num_iid) \
                            .exclude(sku_id__in=sku_ids).update(status=pcfg.DELETE)

                num_iids = []
                prop_dict = {}


@task()
def updateProductWaitPostNumTask(pre_days=UPDATE_WAIT_POST_DAYS):
    """ 更新商品待发数任务 """
    pre_date = datetime.datetime.now() - datetime.timedelta(days=pre_days)
    products = Product.objects.filter(modified__gte=pre_date, status=pcfg.NORMAL)
    for product in products:
        Product.objects.updateProductWaitPostNum(product)


class CalcProductSaleTask(Task):
    """ 更新商品销售数量任务 """

    def getYesterdayDate(self):
        dt = datetime.datetime.now() - datetime.timedelta(days=1)
        return dt.date()

    def getYesterdayStarttime(self, day_date):
        return datetime.datetime(day_date.year, day_date.month, day_date.day, 0, 0, 0)

    def getYesterdayEndtime(self, day_date):
        return datetime.datetime(day_date.year, day_date.month, day_date.day, 23, 59, 59)

    def getSourceList(self, yest_start, yest_end):
        return set(MergeOrder.objects.filter(
            pay_time__gte=yest_start,
            pay_time__lte=yest_end) \
                   .values_list('outer_id', 'outer_sku_id'))

    def getValidUser(self):
        return Seller.effect_users.all()

    def genPaymentQueryset(self, yest_start, yest_end):
        return MergeOrder.objects.filter(
            pay_time__gte=yest_start,
            pay_time__lte=yest_end,
            is_merge=False) \
            .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE) \
            .exclude(merge_trade__sys_status=pcfg.EMPTY_STATUS) \
            .exclude(merge_trade__type=pcfg.EXCHANGE_TYPE, sys_status=pcfg.INVALID_STATUS)

    def genRealQueryset(self, yest_start, yest_end):
        return MergeOrder.objects.filter(
            sys_status=pcfg.IN_EFFECT,
            pay_time__gte=yest_start,
            pay_time__lte=yest_end,
            merge_trade__status__in=pcfg.ORDER_SUCCESS_STATUS) \
            .exclude(gift_type=pcfg.RETURN_GOODS_GIT_TYPE) \
            .exclude(merge_trade__sys_status__in=(pcfg.INVALID_STATUS, pcfg.ON_THE_FLY_STATUS)) \
            .exclude(merge_trade__sys_status=pcfg.FINISHED_STATUS,
                     merge_trade__is_express_print=False)

    def sumQueryset(self, queryset, user, product, sku):
        return queryset.filter(merge_trade__user=user,
                               outer_id=product.outer_id,
                               outer_sku_id=sku and sku.outer_id or '')

    def getTotalRefundFee(self, order_qs):

        effect_oids = [o[0] for o in order_qs.values_list('oid') if len(o[0]) > 6]

        refunds = Refund.objects.filter(oid__in=effect_oids, status__in=(
            pcfg.REFUND_WAIT_SELLER_AGREE, pcfg.REFUND_CONFIRM_GOODS, pcfg.REFUND_SUCCESS))

        return refunds.aggregate(total_refund_fee=Sum('refund_fee')).get('total_refund_fee') or 0

    def calcSaleByUserAndProduct(self, yest_start, yest_end, user, product, sku):

        yest_date = yest_start.date()
        queryset = self.genPaymentQueryset(yest_start, yest_end)
        real_queryset = self.genRealQueryset(yest_start, yest_end)

        sale_queryset = self.sumQueryset(queryset, user, product, sku)
        sale_dict = sale_queryset.aggregate(sale_num=Sum('num'), sale_payment=Sum('payment'))

        real_sale_queryset = self.sumQueryset(real_queryset, user, product, sku)
        real_sale_dict = real_sale_queryset.aggregate(sale_num=Sum('num'), sale_payment=Sum('payment'))

        refund_fee = self.getTotalRefundFee(real_sale_queryset)
        if sale_dict['sale_num']:
            pds, state = ProductDaySale.objects.get_or_create(
                day_date=yest_date,
                user_id=user.id,
                product_id=product.id,
                sku_id=sku and sku.id or 0,
                outer_id=product.outer_id)
            pds.sale_time = product.sale_time or yest_date
            pds.sale_num = sale_dict['sale_num'] or 0
            pds.sale_payment = sale_dict['sale_payment'] or 0
            pds.sale_refund = sale_dict['sale_payment'] - (real_sale_dict['sale_payment'] or 0) + refund_fee
            pds.confirm_num = real_sale_dict['sale_num'] or 0
            pds.confirm_payment = (real_sale_dict['sale_payment'] or 0) - refund_fee
            pds.save()

        return sale_dict['sale_num'] or 0, sale_dict['sale_payment'] or 0

    def run(self, yest_date=None, update_warn_num=False, *args, **kwargs):

        yest_date = yest_date or self.getYesterdayDate()
        yest_start = self.getYesterdayStarttime(yest_date)
        yest_end = self.getYesterdayEndtime(yest_date)

        sellers = self.getValidUser()

        outer_tuple = self.getSourceList(yest_start, yest_end)
        for outer_id, outer_sku_id in outer_tuple:

            prod = Product.objects.getProductByOuterid(outer_id)
            prod_sku = Product.objects.getProductSkuByOuterid(outer_id, outer_sku_id)
            if prod_sku:

                total_sale = 0
                for user in sellers:
                    pds = self.calcSaleByUserAndProduct(yest_start, yest_end, user, prod, prod_sku)
                    total_sale += pds[0]

                if update_warn_num:
                    prod_sku.warn_num = total_sale
                    prod_sku.save()

            if not prod_sku and prod and prod.prod_skus.count() == 0:

                total_sale = 0
                for user in sellers:
                    pds = self.calcSaleByUserAndProduct(yest_start, yest_end, user, prod, None)
                    total_sale += pds[0]

                if update_warn_num:
                    prod.warn_num = total_sale
                    prod.save()

        if update_warn_num:
            products = Product.objects.all()
            for p in products:
                for sku in p.prod_skus.all():
                    if (prod.outer_id, sku.outer_id) not in outer_tuple:
                        sku.warn_num = 0
                        sku.save()

                if p.prod_skus.count() == 0 and (p.outer_id, "") not in outer_tuple:
                    prod.warn_num = total_sale
                    prod.save()


@task()
def updateAllUserProductSkuTask():
    """ 更新所有用户SKU信息任务 """
    users = Seller.effect_users.filter(is_primary=True)
    for user in users:
        subtask(updateUserProductSkuTask).delay(user.visitor_id)


@task()
def updateUserItemsEntityTask(user_id):
    """ 更新用户商品及SKU信息任务 """
    updateUserItemsTask(user_id)

    subtask(updateUserProductSkuTask).delay(user_id)


@task()
def updateAllUserItemsEntityTask():
    """ 更新所有用户商品及SKU信息任务 """
    users = Seller.effect_users.all()
    for user in users:
        subtask(updateUserItemsEntityTask).delay(user.visitor_id)


@task()
def updateUserItemSkuFenxiaoProductTask(user_id):
    """ 更新用户商品信息，SKU信息及分销商品信息任务 """
    updateUserItemsTask(user_id)
    updateUserProductSkuTask(user_id)
    saveUserFenxiaoProductTask(user_id)


@task()
def gradCalcProductSaleTask():
    """  计算商品销售 """

    dt = datetime.datetime.now()
    gradSaleTask = CalcProductSaleTask()
    for day in (10, 20, 30):  # 分别间隔10,20,30天
        delta_days = dt - datetime.timedelta(days=day)
        if settings.DEBUG:
            gradSaleTask(yest_date=delta_days)
        else:
            gradSaleTask.delay(yest_date=delta_days)

    yest_date = dt - datetime.timedelta(days=1)
    # 更新昨日的账单
    if settings.DEBUG:
        CalcProductSaleTask()(yest_date=yest_date, update_warn_num=True)
    else:
        subtask(CalcProductSaleTask()).delay(yest_date=yest_date, update_warn_num=True)


###########################################################  商品库存管理  ########################################################

# @transaction.atomic
def updateItemNum(user_id, num_iid):
    """
    taobao_item_quantity_update response:
    {'iid': '21557036378',
    'modified': '2012-12-26 12:51:16',
    'num': 24,
    'num_iid': 21557036378,
    'skus': {'sku': ({'modified': <type 'str'>,
                      'quantity': <type 'int'>,
                      'sku_id': <type 'int'>},
                     {'modified': <type 'str'>,
                      'quantity': <type 'int'>,
                      'sku_id': <type 'int'>})}}
    """
    item = Item.objects.get(num_iid=num_iid)
    user = item.user
    product = item.product
    if not product or not item.sync_stock:
        return

    user_percent = user.stock_percent
    p_outer_id = product.outer_id
    skus = json.loads(item.skus) if item.skus else None
    if skus:
        for sku in skus.get('sku', []):
            try:
                outer_sku_id = sku.get('outer_id', '')
                outer_id, outer_sku_id = Product.objects.trancecode(p_outer_id, outer_sku_id)

                if p_outer_id != outer_id or sku['status'] != pcfg.NORMAL or not outer_sku_id:
                    continue

                product_sku = product.prod_skus.get(outer_id=outer_sku_id)

                order_nums = 0
                wait_nums = max(product_sku.wait_post_num, 0)
                remain_nums = product_sku.remain_num or 0
                real_num = product_sku.quantity
                sync_num = real_num - wait_nums - remain_nums

                # 如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
                if sync_num > 0 and user_percent > 0:
                    sync_num = int(user_percent * sync_num)
                elif sync_num > 0 and sync_num <= product_sku.warn_num:
                    total_num, user_order_num = MergeOrder.get_yesterday_orders_totalnum(item.user.id,
                                                                                         outer_id,
                                                                                         outer_sku_id)
                    if total_num > 0 and user_order_num > 0:
                        sync_num = int(float(user_order_num) / float(total_num) * sync_num)
                    elif total_num == 0:
                        item_count = Item.objects.filter(outer_id=outer_id,
                                                         approve_status=pcfg.ONSALE_STATUS).count() or 1
                        sync_num = int(sync_num / item_count) or sync_num
                    else:
                        sync_num = (real_num - wait_nums) > 10 and 2 or 0
                elif sync_num > 0:
                    product_sku.is_assign = False
                else:
                    sync_num = 0
                # 当前同步库存值，与线上拍下未付款商品数，哪个大取哪个
                sync_num = max(sync_num, sku.get('with_hold_quantity', 0))
                #                #针对小小派，测试线上库存低量促销效果
                #                if product.outer_id == '3116BG7':
                #                    sync_num = product_sku.warn_num > 0 and min(sync_num,product_sku.warn_num+10) or min(sync_num,15)

                # 同步库存数不为0，或者没有库存警告，同步数量不等于线上库存，并且店铺，商品，规格同步状态正确
                if (not (sync_num == 0 and product_sku.is_assign)
                    and sync_num != sku['quantity']
                    and user.sync_stock
                    and product.sync_stock
                    and product_sku.sync_stock):
                    response = apis.taobao_item_quantity_update(num_iid=item.num_iid,
                                                                quantity=sync_num,
                                                                sku_id=sku['sku_id'],
                                                                tb_user_id=user_id)
                    item_dict = response['item_quantity_update_response']['item']
                    Item.objects.filter(num_iid=item_dict['num_iid']).update(modified=item_dict['modified'],
                                                                             num=sync_num)

                    product_sku.save()
                    ItemNumTaskLog.objects.get_or_create(user_id=user_id,
                                                         outer_id=product.outer_id,
                                                         sku_outer_id=outer_sku_id,
                                                         num=sync_num,
                                                         start_at=item.last_num_updated,
                                                         end_at=datetime.datetime.now())
            except Exception, exc:
                logger.error('sync sku num error!', exc_info=True)

    else:
        order_nums = 0
        outer_id, outer_sku_id = Product.objects.trancecode(p_outer_id, '')

        wait_nums = max(product.wait_post_num, 0)
        remain_nums = product.remain_num or 0
        real_num = product.collect_num
        sync_num = real_num - wait_nums - remain_nums

        # 如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
        if sync_num > 0 and user_percent > 0:
            sync_num = int(user_percent * sync_num)
        elif sync_num > 0 and sync_num <= product.warn_num:
            total_num, user_order_num = MergeOrder.get_yesterday_orders_totalnum(
                item.user.id,
                outer_id,
                outer_sku_id)
            if total_num > 0 and user_order_num > 0:
                sync_num = int(float(user_order_num) / float(total_num) * sync_num)
            elif total_num == 0:
                item_count = Item.objects.filter(outer_id=outer_id,
                                                 approve_status=pcfg.ONSALE_STATUS).count() or 1
                sync_num = int(sync_num / item_count) or sync_num
            else:
                sync_num = (real_num - wait_nums) > 10 and 2 or 0
        elif sync_num > 0:
            product.is_assign = False
        else:
            sync_num = 0

        # 当前同步库存值，与线上拍下未付款商品数，哪个大取哪个
        sync_num = max(sync_num, item.with_hold_quantity)
        # 同步库存数不为0，或者没有库存警告，同步数量不等于线上库存，并且店铺，商品同步状态正确
        if (not (sync_num == 0 and product.is_assign)
            and sync_num != item.num
            and user.sync_stock
            and product.sync_stock):
            response = apis.taobao_item_update(num_iid=item.num_iid,
                                               num=sync_num,
                                               tb_user_id=user_id)

            item_dict = response['item_update_response']['item']
            Item.objects.filter(num_iid=item_dict['num_iid']).update(
                modified=item_dict['modified'],
                num=sync_num)

            product.save()

            ItemNumTaskLog.objects.get_or_create(user_id=user_id,
                                                 outer_id=product.outer_id,
                                                 num=sync_num,
                                                 start_at=item.last_num_updated,
                                                 end_at=datetime.datetime.now())

    Item.objects.filter(num_iid=item.num_iid).update(last_num_updated=datetime.datetime.now())


def getPurchaseSkuNum(product, product_sku):
    wait_nums = product_sku.wait_post_num > 0 and product_sku.wait_post_num or 0
    remain_nums = product_sku.remain_num or 0
    real_num = product_sku.quantity
    sync_num = real_num - wait_nums - remain_nums

    if sync_num > 0 and sync_num <= product_sku.warn_num:
        sync_num = int(sync_num * PURCHASE_STOCK_PERCENT / 2)

    elif sync_num > 0:
        sync_num = PURCHASE_STOCK_PERCENT * sync_num

    else:
        sync_num = 0

    return int(sync_num)


# @transaction.atomic
def updatePurchaseItemNum(user_id, pid):
    """
    {"fenxiao_sku": [{"outer_id": "10410", 
                      "name": "**", 
                      "quota_quantity": 0, 
                      "standard_price": "39.90", 
                      "reserved_quantity": 0, 
                      "dealer_cost_price": "78.32", 
                      "id": 2259034511371, 
                      "cost_price": "35.11", 
                      "properties": "**", 
                      "quantity": 110}]}
    """
    item = FenxiaoProduct.objects.get(pid=pid)
    user = item.user

    try:
        product = Product.objects.get(outer_id=item.outer_id)
    except Product.DoesNotExist:
        product = None

    if not product or not product.sync_stock:
        return

    outer_id = product.outer_id
    skus = json.loads(item.skus) if item.skus else None
    if skus:

        sku_tuple = []
        for sku in skus.get('fenxiao_sku', []):
            outer_sku_id = sku.get('outer_id', '')
            try:
                product_sku = product.prod_skus.get(outer_id=outer_sku_id)
            except:
                continue

            sync_num = getPurchaseSkuNum(product, product_sku)
            sku_tuple.append(('%d' % sku['id'], '%d' % sync_num, outer_sku_id))

        # 同步库存数不为0，或者没有库存警告，同步数量不等于线上库存，并且店铺，商品，规格同步状态正确
        if (sku_tuple and user.sync_stock and product.sync_stock):
            response = apis.taobao_fenxiao_product_update(pid=pid,
                                                          sku_ids=','.join([s[0] for s in sku_tuple]),
                                                          sku_quantitys=','.join([s[1] for s in sku_tuple]),
                                                          tb_user_id=user_id)

            item_dict = response['fenxiao_product_update_response']
            FenxiaoProduct.objects.filter(pid=pid).update(modified=item_dict['modified'])

            for index, sku in enumerate(sku_tuple):
                ItemNumTaskLog.objects.get_or_create(user_id=user_id,
                                                     outer_id=outer_id,
                                                     sku_outer_id='fx%s' % sku[2],
                                                     num=sku[1],
                                                     start_at=item_dict['modified'],
                                                     end_at=item_dict['modified'])

    else:
        order_nums = 0
        wait_nums = product.wait_post_num > 0 and product.wait_post_num or 0
        remain_nums = product.remain_num or 0
        real_num = product.collect_num
        sync_num = real_num - wait_nums - remain_nums

        # 如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
        if sync_num > 0 and sync_num <= product.warn_num:
            sync_num = int(sync_num * PURCHASE_STOCK_PERCENT / 2)
        elif sync_num > 0:
            sync_num = PURCHASE_STOCK_PERCENT * sync_num
        else:
            sync_num = 0
        sync_num = int(sync_num)

        if (not (sync_num == 0 and product.is_assign)
            and user.sync_stock and product.sync_stock):
            response = apis.taobao_fenxiao_product_update(pid=pid,
                                                          quantity=sync_num,
                                                          tb_user_id=user_id)
            item_dict = response['fenxiao_product_update_response']
            FenxiaoProduct.objects.filter(pid=pid).update(
                modified=item_dict['modified'])

            ItemNumTaskLog.objects.get_or_create(user_id=user_id,
                                                 outer_id='',
                                                 num=sync_num,
                                                 start_at=item_dict['modified'],
                                                 end_at=item_dict['modified'])


@task()
def updateUserItemNumTask(user_id):
    updateUserItemsTask(user_id)
    updateUserProductSkuTask(user_id)

    items = Item.objects.filter(user__visitor_id=user_id, approve_status=pcfg.ONSALE_STATUS)
    for item in items:
        try:
            updateItemNum(user_id, item.num_iid)
        except Exception, exc:
            logger.error(u'更新淘宝库存异常:%s' % exc, exc_info=True)


@task()
def updateUserPurchaseItemNumTask(user_id):
    saveUserFenxiaoProductTask(user_id)

    purchase_items = FenxiaoProduct.objects.filter(user__visitor_id=user_id,
                                                   status=pcfg.UP_STATUS)
    for item in purchase_items:
        try:
            updatePurchaseItemNum(user_id, item.pid)
        except Exception, exc:
            logger.error(u'更新分销库存异常:%s' % exc.message, exc_info=True)


@task()
def updateAllUserItemNumTask():
    updateProductWaitPostNumTask()

    for user in Seller.effect_users.TAOBAO:
        updateUserItemNumTask(user.visitor_id)


@task()
def updateAllUserPurchaseItemNumTask():
    updateProductWaitPostNumTask()

    users = Seller.effect_users.TAOBAO.filter(has_fenxiao=True)

    for user in users:
        updateUserPurchaseItemNumTask(user.visitor_id)


from shopback.items.service import releaseProductTrades


@task
def releaseProductTradesTask(outer_ids):
    for outer_id in outer_ids:
        releaseProductTrades(outer_id)


from supplychain.supplier.models import SaleProduct


class CalcProductSaleAsyncTask(Task):
    def getProductByOuterId(self, outer_id):
        try:
            return Product.objects.get(outer_id=outer_id)
        except:
            return None

    def getSaleSortedItems(self, queryset, buyer_name, supplier):

        sale_items = {}
        for sale in queryset:
            product_id = sale.product_id
            sku_id = sale.sku_id

            if product_id in sale_items:
                sale_items[product_id]['sale_num'] += sale.sale_num
                sale_items[product_id]['sale_payment'] += sale.sale_payment
                sale_items[product_id]['sale_refund'] += sale.sale_refund
                sale_items[product_id]['confirm_num'] += sale.confirm_num
                sale_items[product_id]['confirm_payment'] += sale.confirm_payment

                if not sku_id:
                    continue
                skus = sale_items[product_id]['skus']
                if sku_id in skus:
                    skus[sku_id]['sale_num'] += sale.sale_num
                    skus[sku_id]['sale_payment'] += sale.sale_payment
                    skus[sku_id]['sale_refund'] += sale.sale_refund
                    skus[sku_id]['confirm_num'] += sale.confirm_num
                    skus[sku_id]['confirm_payment'] += sale.confirm_payment
                else:
                    skus[sku_id] = {
                        'sale_num': sale.sale_num,
                        'sale_payment': sale.sale_payment,
                        'sale_refund': sale.sale_refund,
                        'confirm_num': sale.confirm_num,
                        'confirm_payment': sale.confirm_payment}
            else:
                product = Product.objects.get(id=product_id)
                pic_path = product.pic_path
                if pic_path.startswith('http://img02.taobaocdn'):
                    pic_path = pic_path.rstrip('_80x80.jpg') + '.jpg_80x80.jpg'
                try:
                    sale_product = SaleProduct.objects.get(id=product.sale_product)
                    contactor = sale_product.contactor.username
                    supplier_name = sale_product.sale_supplier.supplier_name
                except:
                    contactor = ""
                    supplier_name = ""
                if buyer_name:
                    if contactor != buyer_name:
                        continue

                if supplier:
                    if supplier_name != supplier:
                        continue

                sale_items[product_id] = {
                    'pic_path': pic_path,
                    'title': product.title(),
                    'sale_num': sale.sale_num,
                    'sale_payment': sale.sale_payment,
                    'sale_refund': sale.sale_refund,
                    'confirm_num': sale.confirm_num,
                    'confirm_payment': sale.confirm_payment,
                    'contactor': contactor,
                    'supplier': supplier_name,
                    'skus': {}}
                if sku_id:
                    sale_items[product_id]['skus'][sku_id] = {
                        'sale_num': sale.sale_num,
                        'sale_payment': sale.sale_payment,
                        'sale_refund': sale.sale_refund,
                        'confirm_num': sale.confirm_num,
                        'confirm_payment': sale.confirm_payment,
                    }
        return sorted(sale_items.items(), key=lambda d: d[1]['sale_num'], reverse=True)

    def calcSaleSortedItems(self, queryset, buyer_name, supplier):
        total_stock_num = 0
        total_sale_num = 0
        total_sale_payment = 0
        total_confirm_num = 0
        total_confirm_payment = 0
        total_confirm_cost = 0
        total_sale_refund = 0
        total_stock_cost = 0
        sale_stat_list = self.getSaleSortedItems(queryset, buyer_name, supplier)

        for product_id, sale_stat in sale_stat_list:
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                continue

            has_sku = sale_stat['skus'] and True or False
            sale_stat['name'] = product.name
            sale_stat['outer_id'] = product.outer_id
            sale_stat['confirm_cost'] = not has_sku and product.cost * sale_stat['confirm_num'] or 0
            sale_stat['collect_num'] = not has_sku and product.collect_num or 0
            sale_stat['stock_cost'] = not has_sku and product.cost * product.collect_num or 0

            for sku_id, sku_stat in sale_stat['skus'].iteritems():
                try:
                    sku = ProductSku.objects.get(id=sku_id)
                except ProductSku.DoesNotExist:
                    continue
                sku_stat['name'] = sku.name
                sku_stat['outer_id'] = sku.outer_id
                sku_stat['quantity'] = sku.quantity
                sku_stat['confirm_cost'] = sku.cost * sku_stat['confirm_num']
                sku_stat['stock_cost'] = sku.cost * sku.quantity
                sale_stat['confirm_cost'] += sku_stat['confirm_cost']
                sale_stat['collect_num'] += sku.quantity
                sale_stat['stock_cost'] += sku_stat['stock_cost']

            sale_stat['skus'] = sorted(sale_stat['skus'].items(), key=lambda d: d[1]['sale_num'], reverse=True)
            total_stock_num += sale_stat['collect_num']
            total_sale_num += sale_stat['sale_num']
            total_confirm_num += sale_stat['confirm_num']
            total_confirm_payment += sale_stat['confirm_payment']
            total_confirm_cost += sale_stat['confirm_cost']
            total_sale_payment += sale_stat['sale_payment']
            total_sale_refund += sale_stat['sale_refund']
            total_stock_cost += sale_stat['stock_cost']

        return {'sale_items': sale_stat_list,
                'total_confirm_cost': total_confirm_cost,
                'total_confirm_num': total_confirm_num,
                'total_confirm_payment': total_confirm_payment,
                'total_sale_num': total_sale_num,
                'total_sale_refund': total_sale_refund,
                'total_sale_payment': total_sale_payment,
                'total_stock_num': total_stock_num,
                'total_stock_cost': total_stock_cost}

    def calcUnSaleSortedItems(self, queryset, p_outer_id=None):

        total_stock_num = 0
        total_stock_cost = 0
        product_list = Product.objects.filter(status=pcfg.NORMAL)
        if p_outer_id:
            product_list = product_list.filter(outer_id__startswith=p_outer_id)

        ps_tuple = set(queryset.values_list('product_id', 'sku_id').distinct())
        productid_set = set(s[0] for s in ps_tuple)
        sale_items = {}
        for product in product_list:
            product_id = product.id

            if product.collect_num <= 0:
                continue
            try:
                sale_product = SaleProduct.objects.get(id=product.sale_product)
                contactor = sale_product.contactor.username
                supplier = sale_product.sale_supplier.supplier_name
            except:
                contactor = ""
                supplier = ""
            for sku in product.pskus:
                sku_id = sku.id

                if (product_id, sku_id) in ps_tuple or sku.quantity <= 0:
                    continue

                if product_id not in sale_items:
                    sale_items[product_id] = {
                        'sale_num': 0,
                        'sale_payment': 0,
                        'sale_refund': 0,
                        'confirm_num': 0,
                        'confirm_payment': 0,
                        'confirm_cost': 0,
                        'name': product.name,
                        'outer_id': product.outer_id,
                        'sale_cost': 0,
                        'stock_cost': 0,
                        'collect_num': 0,
                        'contactor': contactor,
                        'supplier': supplier,
                        'skus': {}}

                sale_items[product_id]['skus'][sku_id] = {
                    'name': sku.name,
                    'outer_id': sku.outer_id,
                    'quantity': sku.quantity,
                    'sale_cost': 0,
                    'sale_num': 0,
                    'sale_payment': 0,
                    'sale_refund': 0,
                    'confirm_num': 0,
                    'confirm_payment': 0,
                    'confirm_cost': 0,
                    'stock_cost': sku.quantity * sku.cost
                }
                sale_items[product_id]['collect_num'] += sku.quantity
                sale_items[product_id]['stock_cost'] += sku.quantity * sku.cost

            if product_id not in productid_set and not sale_items.has_key(product_id):
                product = Product.objects.get(id=product_id)
                try:
                    sale_product = SaleProduct.objects.get(id=product.sale_product)
                    contactor = sale_product.contactor.username
                    supplier = sale_product.sale_supplier.supplier_name
                except:
                    contactor = ""
                    supplier = ""
                pic_path = product.pic_path
                if pic_path.startswith('http://img02.taobaocdn'):
                    pic_path = pic_path.rstrip('_80x80.jpg') + '.jpg_80x80.jpg'

                sale_items[product_id] = {'pic_path': pic_path,
                                          'title': product.title(),
                                          'sale_num': 0,
                                          'sale_payment': 0,
                                          'sale_refund': 0,
                                          'confirm_num': 0,
                                          'confirm_payment': 0,
                                          'confirm_cost': 0,
                                          'name': product.name,
                                          'outer_id': product.outer_id,
                                          'collect_num': product.collect_num,
                                          'sale_cost': 0,
                                          'contactor': contactor,
                                          'supplier': supplier,
                                          'stock_cost': product.collect_num * product.cost,
                                          'skus': {}}

            if sale_items.has_key(product_id):
                sale_items[product_id]['skus'] = sorted(sale_items[product_id]['skus'].items(),
                                                        key=lambda d: d[1]['quantity'],
                                                        reverse=True)

                total_stock_num += sale_items[product_id]['collect_num']
                total_stock_cost += sale_items[product_id]['stock_cost']

        return {'sale_items': sorted(sale_items.items(),
                                     key=lambda d: d[1]['collect_num'],
                                     reverse=True),
                'total_confirm_cost': 0,
                'total_confirm_num': 0,
                'total_confirm_payment': 0,
                'total_sale_num': 0,
                'total_sale_refund': 0,
                'total_sale_payment': 0,
                'total_stock_num': total_stock_num,
                'total_stock_cost': total_stock_cost}

    def calcSaleItems(self, queryset, buyer_name="", supplier="", p_outer_id=None, show_sale=True):
        if show_sale:
            return self.calcSaleSortedItems(queryset, buyer_name, supplier)

        return self.calcUnSaleSortedItems(queryset, p_outer_id=p_outer_id)

    def run(self, params=None, buyer_name="", supplier="", p_outer_id="", show_sale=True, *args, **kwargs):
        sale_qs = ProductDaySale.objects.filter(**params)
        sale_items = self.calcSaleItems(queryset=sale_qs, buyer_name=buyer_name, supplier=supplier,
                                        p_outer_id=p_outer_id, show_sale=show_sale)
        return sale_items


def get_product_logsign(product):
    return '库存数={0},待发数={1},预留数={2},锁定数={3}'.format(product.collect_num, product.wait_post_num,
                                                    product.remain_num, product.lock_num)


@task()
def task_Auto_Upload_Shelf():
    """ 自动上架商品　"""
    logger = logging.getLogger('celery.handler')
    from core.options import log_action, CHANGE
    from django.contrib.auth.models import User as DjangoUser

    systemoa, state = DjangoUser.objects.get_or_create(username="systemoa", is_active=True)  # 系统用户
    today = datetime.date.today()  # 上架日期
    queryset = Product.objects.filter(sale_time=today, status=Product.NORMAL)  # 今天的正常状态的产品
    unverify_qs = queryset.filter(is_verify=False)  # 今天正常状态产品中没有审核的产品
    upshelf_qs = queryset.filter(is_verify=True, shelf_status=Product.DOWN_SHELF)  # 未上架的产品(并且是已经审核状态产品)
    unverify_no = unverify_qs.count()  # 没有审核的产品数量
    count = 0
    for product in upshelf_qs:
        product.shelf_status = Product.UP_SHELF
        # signals.signal_product_upshelf.send(sender=Product, product_list=[product])  # 发送商品上架消息
        # 上架的信号触发在 items.models pre_save 中已经有保存上架状态变化的时候触发上架信号所以这里注释掉
        product.save()
        log_sign = get_product_logsign(product)  # 生成日志信息
        log_action(systemoa.id, product, CHANGE, u'系统自动上架商品:%s' % log_sign)  # 保存操作日志
        count += 1
    logger.warn("{0}系统自动上架{1}个产品,未通过审核{2}个产品".format(datetime.datetime.now(), count, unverify_no), exc_info=True)


@task()
def task_Auto_Download_Shelf():
    """ 自动下架商品 """
    logger = logging.getLogger('celery.handler')
    from shopback import signals
    from core.options import log_action, CHANGE
    from django.contrib.auth.models import User as DjangoUser
    systemoa, state = DjangoUser.objects.get_or_create(username="systemoa", is_active=True)
    yestoday = datetime.date.today() - datetime.timedelta(days=1)
    queryset = Product.objects.filter(sale_time=yestoday, status=Product.NORMAL)  # 昨天上架的状态正常的产品
    unverify_qs = queryset.filter(is_verify=False)  # 昨天上架状态正常没有审核的
    upshelf_qs = queryset.filter(shelf_status=Product.UP_SHELF)  # 昨天已经上架的产品(包含没有审核状态产品)
    unverify_no = unverify_qs.count()  # 没有审核的产品数量
    count = 0
    for product in upshelf_qs:
        product.shelf_status = Product.DOWN_SHELF
        signals.signal_product_downshelf.send(sender=Product, product_list=[product])
        product.save()
        count += 1
        log_sign = get_product_logsign(product)  # 生成日志信息
        log_action(systemoa.id, product, CHANGE, u'系统自动下架商品:%s' % log_sign)  # 保存操作日志
    logger.warn("{0}系统自动下架{1}个产品,含未通过审核{2}个产品".format(datetime.datetime.now(), count, unverify_no), exc_info=True)


@task()
def task_assign_stock_to_package_sku_item(stat):
    from shopback.trades.models import PackageSkuItem
    available_num = stat.realtime_quantity - stat.assign_num
    if available_num > 0:
        package_sku_items = PackageSkuItem.objects.filter(sku_id=stat.sku_id,
                                                          assign_status=PackageSkuItem.NOT_ASSIGNED,
                                                          num__lte=available_num).order_by('pay_time')
        if package_sku_items.count() > 0:
            package_sku_item = package_sku_items.first()
            package_sku_item.assign_status = PackageSkuItem.ASSIGNED
            package_sku_item.set_assign_status_time()
            package_sku_item.save()


@task()
def task_relase_package_sku_item(stat):
    sku_id = stat.sku_id
    from shopback.trades.models import PackageSkuItem
    pki = PackageSkuItem.objects.filter(sku_id=sku_id, assign_status=PackageSkuItem.ASSIGNED).order_by('-pay_time').first()
    if pki:
        pki.reset_assign_status()


@task()
@transaction.atomic
def task_productsku_update_productskustats(sku_id, product_id):
    stats = ProductSkuStats.objects.filter(sku_id=sku_id)
    if stats.count() <= 0:
        stat = ProductSkuStats(sku_id=sku_id, product_id=product_id)
        stat.save()


@task()
def task_update_productskustats_inferior_num(sku_id):
    from flashsale.dinghuo.models import InBoundDetail, RGDetail, ReturnGoods
    inferior_num = InBoundDetail.objects.filter(sku_id=sku_id, checked=True,
                                                created__gt=ProductSkuStats.PRODUCT_SKU_STATS_COMMIT_TIME). \
        aggregate(n=Sum("inferior_quantity")).get('n', 0)
    inferior_num_add = inferior_num if inferior_num else 0
    inferior_num_plus = RGDetail.get_inferior_total(sku_id)
    stat = ProductSkuStats.get_by_sku(sku_id)
    stat.inferior_num = inferior_num_add - inferior_num_plus
    stat.save(update_fields=['inferior_num'])


@task()
def task_update_inferiorsku_rg_quantity(sku_id):
    from flashsale.dinghuo.models import RGDetail
    rg_quantity = RGDetail.get_inferior_total(sku_id, ProductSkuStats.PRODUCT_SKU_STATS_COMMIT_TIME)
    stat = InferiorSkuStats.get_by_sku(sku_id)
    if stat.rg_quantity != rg_quantity:
        stat.rg_quantity = rg_quantity
        stat.save(update_fields=['rg_quantity'])


@task()
def task_update_inferiorsku_return_quantity(sku_id):
    from shopback.refunds.models import RefundProduct
    quantity = RefundProduct.get_total(sku_id, can_reuse=False,
                                       begin_time=ProductSkuStats.PRODUCT_SKU_STATS_COMMIT_TIME)
    stat = InferiorSkuStats.get_by_sku(sku_id)
    if stat.return_quantity != quantity:
        stat.return_quantity = quantity
        stat.save(update_fields=['return_quantity'])


@task()
def task_update_inferiorsku_inbound_quantity(sku_id):
    from flashsale.dinghuo.models import InBoundDetail
    quantity = InBoundDetail.get_inferior_total(
        sku_id, begin_time=ProductSkuStats.PRODUCT_SKU_STATS_COMMIT_TIME)
    stat = InferiorSkuStats.get_by_sku(sku_id)
    if stat.inbound_quantity != quantity:
        stat.inbound_quantity = quantity
        stat.save(update_fields=['inbound_quantity'])


# @task()
def task_stock_adjust_update_productskustats_inferior_num(sku_id, product_id):
    pass


@task(max_retries=3, default_retry_delay=5)
def task_auto_shelf_prods():
    """
    1. 自动上架产品：　已经审核的产品　并且在下架状态的产品　修改状态到上架
    2. 自动下架产品：　并且在上架状态的产品　修改状态到下架状态
    """
    try:
        from supplychain.supplier.models import SaleProductManage, SaleProductManageDetail
        today = datetime.date.today()
        schedules = SaleProductManage.objects.filter(sale_time=today)
        sale_product_ids = []   # 要上架的排期管理选品id
        for schedule in schedules:
            sale_product_ids += [d.sale_product_id for d in
                                 schedule.manage_schedule.filter(today_use_status=SaleProductManageDetail.NORMAL)]

        systemoa = get_systemoa_user()
        offshelf_models = ModelProduct.offshelf_right_now_models()
        onshelf_models = ModelProduct.upshelf_right_now_models()
        onshelf_models = onshelf_models.filter(saleproduct_id__in=sale_product_ids)

        offshelf_pros = Product.offshelf_right_now_products()  # 要立即下架的产品
        onshelf_pros = Product.upshelf_right_now_products()  # 要立即上架的产品
        onshelf_pros = onshelf_pros.filter(sale_product__in=sale_product_ids)

        logger.warn({
            'action': 'auto_off_shelf_models',
            'auto_off_shelf_models_ids': ','.join([str(x[0]) for x in offshelf_models.values_list('id')]),
            'auto_off_shelf_models_count': offshelf_models.count()})  # 下架款式log记录

        for off_md in offshelf_models:
            state_off = off_md.offshelf_model()
            if state_off:
                log_action(systemoa, off_md, CHANGE, u'系统自动下架款式')

        logger.warn({
            'action': 'auto_off_shelf_pros',
            'auto_off_shelf_pros_ids': ','.join([str(x[0]) for x in offshelf_pros.values_list('id')]),
            'auto_off_shelf_pros_count': offshelf_pros.count()
        })  # 下架产品log记录

        for off_pro in offshelf_pros:
            state = off_pro.offshelf_product()  # 执行下架动作
            if state:  # 上架成功　打log
                log_action(systemoa, off_pro, CHANGE, u'系统自动下架修改该产品到下架状态')

        logger.warn({
            'action': 'auto_on_shelf_models',
            'auto_on_shelf_models_ids': ','.join([str(x[0]) for x in onshelf_models.values_list('id')]),
            'auto_on_shelf_models_count': onshelf_models.count()
        })  # 上架款式log记录

        for on_md in onshelf_models:
            state_on = on_md.upshelf_model()
            if state_on:
                log_action(systemoa, on_md, CHANGE, u'系统自动上架款式')

        logger.warn({
            'action': 'auto_on_shelf_prods',
            'auto_on_shelf_prods_ids': ','.join([str(x[0]) for x in onshelf_pros.values_list('id')]),
            'auto_on_shelf_prods_count': onshelf_pros.count()
        })

        for on_pro in onshelf_pros:
            state = on_pro.upshelf_product()  # 执行上架动作
            if state:  # 上架成功　打log
                log_action(systemoa, on_pro, CHANGE, u'系统自动上架修改该产品到上架状态')

    except Exception as exc:
        raise task_auto_shelf_prods.retry(countdown=60 * 5, exc=exc)


@task()
def task_productskustats_update_productsku(stats):
    sku_id = stats.sku_id
    psku = ProductSku.objects.get(id=sku_id)
    if psku.lock_num != stats.lock_num:
        psku.lock_num = stats.lock_num
        psku.save(update_fields=['lock_num'])


@task()
def task_supplier_update_product_ware_by(supplier):
    from shopback.items.models import Product
    spids = [i.id for i in supplier.supplier_products.all()]
    Product.objects.filter(sale_product__in=spids).update(ware_by=supplier.ware_by)