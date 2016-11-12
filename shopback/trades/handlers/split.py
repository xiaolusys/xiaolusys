# -*- coding:utf8 -*-
from django.conf import settings
from .handler import BaseHandler
from shopback.trades.models import MergeTrade
from shopapp.memorule import ruleMatchPayment, ruleMatchSplit, ruleMatchGifts
from shopback import paramconfig as pcfg
from common.modelutils import update_model_fields

import logging

logger = logging.getLogger('celery.handler')


class SplitHandler(BaseHandler):
    """
        线上商品编码，内部商品编码映射,拆分，附赠品
    """

    def handleable(self, merge_trade, *args, **kwargs):
        return kwargs.get('first_pay_load', None)

    def process(self, merge_trade, *args, **kwargs):
        logger.debug('DEBUG SPLIT:%s' % merge_trade)

        # 组合拆分
        ruleMatchSplit(merge_trade)

        # 金额匹配
        ruleMatchPayment(merge_trade)

        # 买就送
        ruleMatchGifts(merge_trade)
