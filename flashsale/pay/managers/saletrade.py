# coding=utf-8
from __future__ import unicode_literals, absolute_import
from core.managers import BaseManager
import logging

logger = logging.getLogger(__name__)


class NormalSaleTradeManager(BaseManager):
    def get_queryset(self):
        _super = super(NormalSaleTradeManager, self)
        queryset = _super.get_queryset()
        return queryset.filter(status__in=self.model.NORMAL_TRADE_STATUS).order_by('-created')


class NormalSaleOrderManager(BaseManager):

    def active_orders(self):
        """ 包含已付款,或者已经换货生成的订单(不包含被换货的订单,包含退款订单) """
        queryset = self.get_queryset()
        return queryset.filter(pay_time__isnull=False)\
            .exclude(status__in=self.model.NOPAYMENT_STATUS)

