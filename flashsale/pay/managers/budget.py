# coding=utf-8
from __future__ import unicode_literals, absolute_import
from core.managers import BaseManager
import logging

logger = logging.getLogger(__name__)


class BudgetLogManager(BaseManager):
    def get_pending_budget_logs(self):
        # type: () -> Optional[List[BudgetLog]]
        """待确定的　钱包　记录
        """
        return self.get_queryset().filter(status=self.model.PENDING)

    def get_refund_postage_budget_logs(self):
        # type: () -> Optional[List[BudgetLog]]
        return self.get_queryset().filter(budget_log_type=self.model.BG_REFUND_POSTAGE)

    def get_pending_return_boutique_coupon(self):
        # type: () -> Optional[List[BudgetLog]]
        """获取　待确定　的　精品券　退券退钱　　钱包记录
        """
        return self.get_pending_budget_logs().filter(budget_log_type=self.model.BG_RETURN_COUPON)
