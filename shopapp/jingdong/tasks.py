# -*- coding:utf8 -*-
import time
import datetime
import json
from celery.task import task
from .models import JDShop, JDOrder, JDProduct, JDLogistic
from .service import JDShopService
from .apis import api
from .utils import group_list, update_model_fields
import logging

logger = logging.getLogger('celery.handler')


@task
def pullJDProductByVenderidTask(vender_id, ware_status=1):
    page = 1
    page_size = 100
    has_next = True
    wave_ids = []

    while has_next:

        ware_response = api.jd_wares_search(ware_status=ware_status,
                                            page=page,
                                            page_size=page_size,
                                            jd_user_id=vender_id)

        has_next = ware_response['total'] > page * page_size
        page += 1
        iwave_ids = []

        for ware in ware_response['ware_infos']:

            jd_product, state = JDProduct.objects.get_or_create(ware_id=ware['ware_id'])

            for k, v in ware.iteritems():
                hasattr(jd_product, k) and setattr(jd_product, k, v)

            jd_product.online_time = ware.get('online_time') or None
            jd_product.offline_time = ware.get('offline_time') or None
            jd_product.modified = ware.get('modified') or None

            jd_product.save()

            iwave_ids.append(ware['ware_id'])

        for wave_id_list in group_list(iwave_ids, 10):

            wave_list = api.jd_wares_list_get(ware_ids=','.join([str(w) for w in wave_id_list])
                                              , fields='ware_id,skus'
                                              , jd_user_id=vender_id)

            for ware in wave_list['wares']:
                ware_skus = json.dumps(ware['skus'])

                JDProduct.objects.filter(ware_id=ware['ware_id']).update(skus=ware_skus)

        wave_ids.extend(iwave_ids)

    if ware_status:
        JDProduct.objects.filter(ware_status=JDProduct.ON_SALE) \
            .exclude(ware_id__in=wave_ids) \
            .update(ware_status=JDProduct.SYSTEM_DOWN)


@task
def pullJDLogisticByVenderidTask(vender_id):
    from shopback.users.models import User

    logistic_list = api.jd_delivery_logistics_get(jd_user_id=vender_id)

    for logistic in logistic_list['logistics_list']:

        jd_logistic, state = JDLogistic.objects.get_or_create(
            logistics_id=logistic['logistics_id'])

        for k, v in logistic.iteritems():
            hasattr(jd_logistic, k) and setattr(jd_logistic, k, v)

        jd_logistic.save()


@task
def pullJDOrderByModifiedTask(jd_shop, status_list, begintime=None, endtime=None):
    page = 1
    page_size = 2
    has_next = True

    while has_next:
        response = api.jd_order_search(start_date=begintime,
                                       end_date=endtime,
                                       order_state=','.join(status_list),
                                       page=page,
                                       page_size=page_size,
                                       jd_user_id=jd_shop.vender_id)

        has_next = response['order_total'] > page * page_size
        page += 1

        for order_dict in response['order_info_list']:
            jd_order = JDShopService.createTradeByDict(jd_shop.vender_id,
                                                       order_dict)

            JDShopService.createMergeTrade(jd_order)


@task
def pullJDOrderByVenderIdTask(vender_id, status_list=[JDOrder.ORDER_STATE_WSTO]):
    jd_shop = JDShop.objects.get(vender_id=vender_id)

    if not jd_shop.order_updated:
        pullJDOrderByModifiedTask(jd_shop, status_list)
        return

    endtime = datetime.datetime.now()

    pullJDOrderByModifiedTask(jd_shop,
                              status_list,
                              begintime=jd_shop.order_updated,
                              endtime=endtime)

    jd_shop.updateOrderUpdated(endtime)


@task
def pullAllJDShopOrderByModifiedTask(status_list=[JDOrder.ORDER_STATE_WSTO,
                                                  JDOrder.ORDER_STATE_FL,
                                                  JDOrder.ORDER_STATE_TC]):
    from shopback.users.models import User

    for user in User.effect_users.JINGDONG:
        pullJDOrderByVenderIdTask(user.visitor_id)


@task
def syncWareStockByJDShopTask(jd_ware):
    """
    """
    from shopback.items.models import Product, ProductSku, ItemNumTaskLog
    from shopback.trades.models import MergeOrder
    from shopback.users.models import User

    if not isinstance(jd_ware, JDProduct):
        jd_ware = JDProduct.objects.get(ware_id=jd_ware)

    if not jd_ware.sync_stock:
        return

    jd_user = User.objects.get(visitor_id=jd_ware.vender_id)

    user_percent = jd_user.stock_percent
    skus = jd_ware.skus and json.loads(jd_ware.skus) or []
    sku_stock_list = []

    for sku in skus:

        if sku['status'] != JDProduct.VALID or not sku.get('outer_id', None):
            continue

        outer_id, outer_sku_id = Product.objects.trancecode('', sku['outer_id'])

        product = Product.objects.get(outer_id=outer_id)
        product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                             product__outer_id=outer_id)

        if not (jd_user.sync_stock and product.sync_stock and product_sku.sync_stock):
            continue

        order_nums = 0
        wait_nums = (product_sku.wait_post_num > 0 and
                     product_sku.wait_post_num or 0)
        remain_nums = product_sku.remain_num or 0
        real_num = product_sku.quantity
        sync_num = real_num - wait_nums - remain_nums

        # 如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
        if sync_num > 0 and user_percent > 0:
            sync_num = int(user_percet * sync_num)

        elif sync_num > 0 and sync_num <= product_sku.warn_num:
            total_num, user_order_num = MergeOrder.get_yesterday_orders_totalnum(jd_user.id,
                                                                                 outer_id,
                                                                                 outer_sku_id)
            if total_num > 0 and user_order_num > 0:
                sync_num = int(float(user_order_num) / float(total_num) * sync_num)

            else:
                sync_num = (real_num - wait_nums) > 10 and 2 or 0

        elif sync_num > 0:
            product_sku.is_assign = False

            update_model_fields(product_sku, update_fields=['is_assign'])
        else:
            sync_num = 0

        #        #针对小小派，测试线上库存低量促销效果
        #        if product.outer_id == '3116BG7':
        #            sync_num = product_sku.warn_num > 0 and min(sync_num,product_sku.warn_num+10) or min(sync_num,15)
        #
        if product_sku.is_assign:
            sync_num = 0

        # 同步库存数不为0，或者没有库存警告，同步数量不等于线上库存，并且店铺，商品，规格同步状态正确
        if (sync_num != sku['stock_num']):
            api.jd_sku_stock_update(outer_id=sku['outer_id'],
                                    quantity=sync_num,
                                    jd_user_id=jd_user.visitor_id)

            ItemNumTaskLog.objects.get_or_create(user_id=jd_user.user.id,
                                                 outer_id=outer_id,
                                                 sku_outer_id='jd%s' % outer_sku_id,
                                                 num=sync_num,
                                                 end_at=datetime.datetime.now())


@task
def syncJDUserWareNumTask(jd_user):
    jd_wares = JDProduct.objects.filter(vender_id=jd_user.visitor_id,
                                        ware_status=JDProduct.ON_SALE)

    for jd_ware in jd_wares:
        syncWareStockByJDShopTask(jd_ware)


@task
def syncAllJDUserWareNumTask():
    from shopback.users.models import User

    for jd_user in User.effect_users.JINGDONG:
        pullJDProductByVenderidTask(jd_user.visitor_id)
        syncJDUserWareNumTask(jd_user)
