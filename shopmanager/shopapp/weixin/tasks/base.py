# -*- coding:utf-8 -*-
import time
import datetime
import json
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings

from common.utils import update_model_fields, replace_utf8mb4
from core.weixin import options
from shopapp.weixin.models import WeiXinUser, WXOrder, WXProduct, WXProductSku, WXLogistic, WeixinUnionID
from shopapp.weixin.weixin_apis import WeiXinAPI, WeiXinRequestException
from shopback.items.models import Product, ItemNumTaskLog

import logging

logger = logging.getLogger(__name__)


def update_weixin_productstock():
    products = Product.objects.filter(shelf_status=1, sale_time=datetime.date.today() - datetime.timedelta(days=1))
    wx_api = WeiXinAPI()

    cnt = 0
    for product in products[18:]:
        cnt += 1

        wx_skus = WXProductSku.objects.filter(outer_id=product.outer_id).order_by('-modified')
        if wx_skus.count() > 0:
            try:
                wx_pid = wx_skus[0].product_id
                WXProduct.objects.getOrCreate(wx_pid, force_update=True)
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                continue
        for sku in product.pskus:
            outer_id = product.outer_id
            outer_sku_id = sku.outer_id
            sync_num = sku.remain_num - sku.wait_post_num
            if sync_num < 0:
                sync_num = 0
            try:
                wx_skus = WXProductSku.objects.filter(outer_id=outer_id,
                                                      outer_sku_id=outer_sku_id)
                for wx_sku in wx_skus:

                    vector_num = sync_num - wx_sku.sku_num
                    if vector_num == 0: continue
                    if vector_num > 0:
                        wx_api.addMerchantStock(wx_sku.product_id,
                                                vector_num,
                                                sku_info=wx_sku.sku_id)
                    else:
                        wx_api.reduceMerchantStock(wx_sku.product_id,
                                                   abs(vector_num),
                                                   sku_info=wx_sku.sku_id)

                    ItemNumTaskLog.objects.get_or_create(user_id=7,
                                                         outer_id=outer_id,
                                                         sku_outer_id='wx%s' % outer_sku_id,
                                                         num=sync_num,
                                                         end_at=datetime.datetime.now())
            except Exception, exc:
                logger.error(exc.message, exc_info=True)


@task(max_retries=3, default_retry_delay=60)
def task_Update_Weixin_Userinfo(openId, unionId=None, userinfo={}, accessToken=None):
    """ 通过接口获取用户信息 """
    _wx_api = WeiXinAPI()
    if accessToken and not userinfo:
        userinfo = options.get_weixin_snsuserinfo(openId, accessToken)
    elif not userinfo:
        userinfo = _wx_api.getUserInfo(openId)

    wx_user, state = WeiXinUser.objects.get_or_create(openid=openId)
    pre_subscribe_time = wx_user.subscribe_time

    pre_nickname = wx_user.nickname
    for k, v in userinfo.iteritems():
        if hasattr(wx_user, k) and v:
            setattr(wx_user, k, v or getattr(wx_user, k))

    wx_user.nickname = pre_nickname or replace_utf8mb4(wx_user.nickname.decode('utf8'))
    wx_user.unionid = wx_user.unionid or unionId or ''
    subscribe_time = userinfo.get('subscribe_time', None)
    if subscribe_time:
        wx_user.subscribe_time = pre_subscribe_time or datetime.datetime \
            .fromtimestamp(int(subscribe_time))

    key_list = ['openid', 'sex', 'language', 'headimgurl', 'country', 'province', 'nickname', 'unionid',
                'subscribe_time', 'sceneid']
    update_model_fields(wx_user, update_fields=key_list)

    if not wx_user.unionid:
        return

    app_key = _wx_api._wx_account.app_id
    WeixinUnionID.objects.get_or_create(openid=openId, app_key=app_key, unionid=wx_user.unionid)


@task(max_retries=3, default_retry_delay=60)
def task_Mod_Merchant_Product_Status(outer_ids, status):
    from shopback.items.models import Product
    from shopback import signals


    exception = None
    for outer_id in outer_ids:
        # update_wxpids = set([])
        # _wx_api = WeiXinAPI()
        ###############################
        #         try:
        #             wx_skus = WXProductSku.objects.filter(outer_id=outer_id).values('product').distinct()
        #             wx_prodids = [p['product'] for p in wx_skus]
        #
        #             wx_prods = WXProduct.objects.filter(product_id__in=wx_prodids).order_by('-modified')
        #             if wx_prods.count() == 0 :
        #                 raise Exception(u'未找到商品编码(%s)对应线上小店商品'%outer_id)
        #
        #             wx_product = wx_prods[0]
        #             wxproduct_id = wx_product.product_id
        #             if wxproduct_id not in update_wxpids:
        #                 update_wxpids.add(wxproduct_id)
        #                 _wx_api.modMerchantProductStatus(wxproduct_id, status)
        #
        #         except Exception, exc:
        #             exception = exc

        product = Product.objects.get(outer_id=outer_id)

        if status == WXProduct.UP_ACTION:
            product.shelf_status = Product.UP_SHELF
            # 发送商品上架消息
            signals.signal_product_upshelf.send(sender=Product, product_list=[product])
        else:
            product.shelf_status = Product.DOWN_SHELF
            signals.signal_product_downshelf.send(sender=Product, product_list=[product])
        product.save()

    if exception:
        raise exception


@task
def pullWXProductTask():
    _wx_api = WeiXinAPI()
    products = _wx_api.getMerchantByStatus(0)
    up_shelf_ids = []

    for product in products:
        WXProduct.objects.createByDict(product)
        up_shelf_ids.append(product['product_id'])

    WXProduct.objects.exclude(product_id__in=up_shelf_ids) \
        .update(status=WXProduct.DOWN_SHELF)


@task
def pullWaitPostWXOrderTask(begintime, endtime, full_update=False):

    from shopapp.weixin.service import WxShopService

    update_status = [  # WXOrder.WX_WAIT_PAY,
        WXOrder.WX_WAIT_SEND,
        WXOrder.WX_WAIT_CONFIRM,
        WXOrder.WX_FINISHED]

    _wx_api = WeiXinAPI()

    if not begintime and _wx_api._wx_account.order_updated:
        begintime = int(
            time.mktime((_wx_api._wx_account.order_updated - datetime.timedelta(seconds=6 * 60 * 60)).timetuple()))

    dt = datetime.datetime.now()
    endtime = endtime and endtime or int(time.mktime(dt.timetuple()))

    if full_update:
        begintime = None
        endtime = None

    for status in update_status:
        orders = _wx_api.getOrderByFilter(status=status, begintime=begintime, endtime=endtime)

        for order_dict in orders:
            order = WxShopService.createTradeByDict(_wx_api._wx_account.account_id, order_dict)
            WxShopService.createMergeTrade(order)

    _wx_api._wx_account.changeOrderUpdated(dt)


@task
def pullFeedBackWXOrderTask(begintime, endtime):

    from shopapp.weixin.service import WxShopService

    _wx_api = WeiXinAPI()

    if not begintime and _wx_api._wx_account.refund_updated:
        begintime = int(time.mktime(_wx_api._wx_account.refund_updated.timetuple()))

    dt = datetime.datetime.now()
    endtime = endtime and endtime or int(time.mktime(dt.timetuple()))

    orders = _wx_api.getOrderByFilter(WXOrder.WX_FEEDBACK, begintime, endtime)

    for order_dict in orders:
        order = WxShopService.createTradeByDict(_wx_api._wx_account.account_id,
                                                order_dict)

        WxShopService.createMergeTrade(order)

    _wx_api._wx_account.changeRefundUpdated(dt)


@task
def syncStockByWxShopTask(wx_product):
    from shopback.items.models import Product, ProductSku, ItemNumTaskLog
    from shopback.trades.models import MergeOrder
    from shopback.users.models import User

    if not isinstance(wx_product, WXProduct):
        wx_product = WXProduct.objects.get(product_id=wx_product)

    if not wx_product.sync_stock:
        return

    wx_api = WeiXinAPI()

    wx_openid = wx_api.getAccountId()
    wx_user = User.objects.get(visitor_id=wx_openid)

    user_percent = wx_user.stock_percent

    skus = wx_product.sku_list or []

    for sku in skus:

        if not sku.get('product_code', None):
            continue

        try:
            outer_id, outer_sku_id = Product.objects.trancecode('',
                                                                sku['product_code'],
                                                                sku_code_prior=True)

            # 特卖商品暂不同步库存
            if outer_id.startswith(('1', '8', '9')) and len(outer_id) >= 9:
                continue

            product = Product.objects.get(outer_id=outer_id)
            product_sku = ProductSku.objects.get(outer_id=outer_sku_id,
                                                 product__outer_id=outer_id)
        except:
            continue

        if not (wx_user.sync_stock and product.sync_stock and product_sku.sync_stock):
            continue

        wait_nums = (product_sku.wait_post_num > 0 and
                     product_sku.wait_post_num or 0)
        remain_nums = product_sku.remain_num or 0
        real_num = product_sku.quantity
        sync_num = real_num - wait_nums - remain_nums

        # 如果自动更新库存状态开启，并且计算后库存不等于在线库存，则更新
        if sync_num > 0 and user_percent > 0:
            sync_num = int(user_percent * sync_num)

        elif sync_num > 0 and sync_num <= product_sku.warn_num:
            total_num, user_order_num = MergeOrder.get_yesterday_orders_totalnum(wx_user.id,
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
        if (sync_num != sku['quantity']):

            vector_num = sync_num - sku['quantity']

            if vector_num > 0:
                wx_api.addMerchantStock(wx_product.product_id,
                                        vector_num,
                                        sku_info=sku['sku_id'])
            else:
                wx_api.reduceMerchantStock(wx_product.product_id,
                                           abs(vector_num),
                                           sku_info=sku['sku_id'])

            ItemNumTaskLog.objects.get_or_create(user_id=wx_user.user.id,
                                                 outer_id=outer_id,
                                                 sku_outer_id='wx%s' % outer_sku_id,
                                                 num=sync_num,
                                                 end_at=datetime.datetime.now())


@task
def syncWXProductNumTask():
    pullWXProductTask()

    wx_products = WXProduct.objects.filter(status=WXProduct.UP_SHELF)

    for wx_product in wx_products:
        syncStockByWxShopTask(wx_product)


from core.weixin.options import valid_openid


@task
def task_snsauth_update_weixin_userinfo(userinfo, appid):
    """
    Every time we have snsauth userfinfo, we update WeixinUserInfo.
    -- Zifei 2016-04-12
    """

    nick = userinfo.get("nickname")
    thumbnail = userinfo.get("headimgurl")
    unionid = userinfo.get("unionid")
    openid = userinfo.get("openid")

    if not unionid:
        return

    from shopapp.weixin.models_base import WeixinUserInfo
    records = WeixinUserInfo.objects.filter(unionid=unionid)
    if records.count() <= 0:
        info = WeixinUserInfo(unionid=unionid, nick=nick, thumbnail=thumbnail)
        info.save()
    try:
        WeixinUnionID.objects.get(unionid=unionid)
    except WeixinUnionID.DoesNotExist:
        if valid_openid(openid) and valid_openid(unionid):
            WeixinUnionID.objects.create(openid=openid, app_key=appid, unionid=unionid)
    except WeixinUnionID.MultipleObjectsReturned, exc:
        pass
    except Exception, exc:
        logger.info(str(exc), exc_info=True)
    else:
        info = records[0]
        update = False
        if nick and nick != info.nick:
            info.nick = nick
            update = True
        if thumbnail and thumbnail != info.thumbnail:
            info.thumbnail = thumbnail
            update = True
        if update:
            # We must use save() so that it will trigger updating customer.
            info.save()


@task(max_retries=3, default_retry_delay=60)
def task_refresh_weixin_access_token():
    appkeys = [
       settings.WXPAY_APPID,
       settings.WEIXIN_APPID,
    ]

    wx_api = WeiXinAPI()
    for appkey in appkeys:
        try:
            wx_api.setAccountId(appKey=appkey)
            wx_api.refresh_token()
            wx_api.refreshJSTicket()
        except Exception, exc:
            logger.error('task_refresh_weixin_access_token error: %s'%exc)
