# -*- coding:utf8 -*-
import os
from django.conf import settings
from django.db.models import Q

from .handler import BaseHandler
from shopback import paramconfig as pcfg
from core.options import log_action, User, ADDITION, CHANGE
from common.modelutils import update_model_fields

from shopapp.intercept.models import InterceptTrade
import logging

logger = logging.getLogger('celery.handler')


class InterceptHandler(BaseHandler):
    def handleable(self, merge_trade, *args, **kwargs):

        if not kwargs.get('first_pay_load', None):
            return False

        itrades = InterceptTrade.objects.getInterceptTradeByBuyerInfo(merge_trade.buyer_nick,
                                                                      merge_trade.receiver_mobile,
                                                                      merge_trade.tid)

        return itrades.count() > 0

    def process(self, merge_trade, *args, **kwargs):

        logger.debug('DEBUG INTERCEPT:%s' % merge_trade)

        itrades = InterceptTrade.objects.getInterceptTradeByBuyerInfo(
            merge_trade.buyer_nick.strip(),
            merge_trade.receiver_mobile.strip(),
            merge_trade.tid)

        for itrade in itrades:
            itrade.trade_id = merge_trade.id
            itrade.status = InterceptTrade.COMPLETE
            itrade.save()

        merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)
        merge_trade.sys_memo += u'【订单被拦截】'

        update_model_fields(merge_trade, update_fields=['sys_memo'])

        log_action(merge_trade.user.user.id, merge_trade, CHANGE, u'订单被拦截')
