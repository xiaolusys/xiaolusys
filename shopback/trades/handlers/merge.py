# -*- coding:utf8 -*-
import datetime
from django.conf import settings
from .handler import BaseHandler
from shopback.trades.models import MergeTrade
from shopback.items.models import Product
from shopback import paramconfig as pcfg
from shopapp.memorule import ruleMatchPayment
from common.modelutils import update_model_fields

import logging

logger = logging.getLogger('celery.handler')


class MergeHandler(BaseHandler):
    def handleable(self, merge_trade, *args, **kwargs):
        """ 
        判断合并的条件:
         1，非秒杀订单；2，订单商品同仓；3，合单FLAG为True;4，订单第一次入库或地址更新；5，预测是否能合单；
        """
        # 秒杀订单 取消合并
        if (merge_trade.user.visitor_id.lower().endswith('miaosha')
            or merge_trade.user.nick.find(u'秒杀') >= 0):
            return False

        # 判断订单商品是否同仓
        pre_ware = None
        for order in merge_trade.normal_orders:
            try:
                cur_ware = Product.objects.get(outer_id=order.outer_id).ware_by
                if pre_ware and pre_ware != cur_ware:
                    return False
                pre_ware = cur_ware
            except:
                return False

        return (kwargs.get('trade_merge_flag', True) and
                (kwargs.get('first_pay_load', None) or
                 kwargs.get('update_address', None)) and
                MergeTrade.objects.isTradeMergeable(merge_trade))

    def process(self, merge_trade, *args, **kwargs):

        logger.debug('DEBUG MERGE:%s' % merge_trade)

        main_trade = None
        if merge_trade.type in (MergeTrade.WX_TYPE, MergeTrade.SALE_TYPE):
            latest_paytime = datetime.datetime(merge_trade.pay_time.year
                                               , merge_trade.pay_time.month
                                               , merge_trade.pay_time.day)

            merge_queryset = MergeTrade.objects.getMergeQueryset(
                merge_trade.buyer_nick,
                merge_trade.receiver_name,
                merge_trade.receiver_mobile,
                merge_trade.receiver_phone,
                ware_by=merge_trade.ware_by,
                latest_paytime=latest_paytime)

            if merge_queryset.count() == 1:
                return
            merge_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
            main_trade = MergeTrade.objects.driveMergeTrade(merge_trade,
                                                            latest_paytime=latest_paytime)

        else:
            merge_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
            main_trade = MergeTrade.objects.driveMergeTrade(merge_trade)

        if main_trade:
            ruleMatchPayment(main_trade)
