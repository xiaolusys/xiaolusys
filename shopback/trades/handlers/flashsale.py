# -*- coding:utf8 -*-
import os
import datetime
from django.conf import settings
from django.db.models import Q

from .handler import BaseHandler
from shopback import paramconfig as pcfg
from core.options import log_action, User, ADDITION, CHANGE

import logging

logger = logging.getLogger('celery.handler')


class FlashSaleHandler(BaseHandler):
    def handleable(self, merge_trade, *args, **kwargs):

        if merge_trade.type == pcfg.SALE_TYPE:
            return True

        return False

    def process(self, merge_trade, *args, **kwargs):

        logger.debug('DEBUG FlashSale:%s' % merge_trade)

        if not kwargs.get('first_pay_load', None):
            return

        from shopback.items.models import ProductSku, ItemNumTaskLog
        from shopapp.weixin.models import WXProduct, WXProductSku
        from shopapp.weixin.apis import WeiXinAPI
        from shopback.users.models import User

        wx_api = WeiXinAPI()

        tuple_ids = set([(o[0], o[1]) for o in merge_trade.normal_orders.values_list('outer_id', 'outer_sku_id')])
        outer_set = set([])
        for outer_id, outer_sku_id in tuple_ids:
            wx_skus = WXProductSku.objects.filter(outer_id=outer_id,
                                                  outer_sku_id=outer_sku_id,
                                                  status=WXProductSku.UP_SHELF).order_by('-modified')
            if wx_skus.count() == 0:
                continue

            sku = wx_skus[0]
            wxproduct = sku.product
            if sku.outer_id in outer_set:
                outer_set.add(outer_id)
                WXProduct.objects.createByDict(wxproduct)

        oauser = User.getSystemOAUser()
        for outer_id, outer_sku_id in tuple_ids:
            wx_skus = WXProductSku.objects.filter(outer_id=outer_id,
                                                  outer_sku_id=outer_sku_id,
                                                  status=WXProductSku.UP_SHELF)
            if wx_skus.count() == 0:
                continue

            try:
                sku = ProductSku.objects.get(product__outer_id=outer_id, outer_id=outer_sku_id)
                sync_num = sku.remain_num - sku.wait_post_num
                if sync_num < 0:
                    continue

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

                    ItemNumTaskLog.objects.get_or_create(user_id=oauser.id,
                                                         outer_id=outer_id,
                                                         sku_outer_id='wx%s' % outer_sku_id,
                                                         num=sync_num,
                                                         end_at=datetime.datetime.now())

            except Exception, exc:
                logger.error(exc.message, exc_info=True)
