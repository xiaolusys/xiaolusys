# coding=utf-8
from __future__ import unicode_literals, absolute_import
from core.managers import BaseManager
import logging

logger = logging.getLogger(__name__)


class BudgetLogManager(BaseManager):
    def get_refund_postage_budget_logs(self):
        # type: () -> List[BudgetLog]
        return self.get_queryset().filter(budget_log_type=self.model.BG_REFUND_POSTAGE)