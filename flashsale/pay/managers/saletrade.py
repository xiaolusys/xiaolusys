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
