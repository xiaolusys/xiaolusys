# coding=utf-8
__author__ = 'meron'
from django.core.management.base import BaseCommand

from flashsale.pay.models import UserBudget,BudgetLog,SaleTrade,TradeCharge
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.debug('check repeat userbudget and charge start ...')
    blogs = BudgetLog.objects.filter(budget_log_type=BudgetLog.BG_CONSUM,
                             status__in=(BudgetLog.PENDING,BudgetLog.CONFIRMED))
    recharge_list = []
    for bg in blogs:
        st = SaleTrade.objects.get(id=bg.referal_id)
        charge = TradeCharge.objects.filter(order_no=st.tid,paid=True).first()
        if charge  and st.payment > 1 and (int(st.payment * 100) - bg.flow_amount) < 10:
            recharge_list.append((st.tid,bg))
    logger.debug('recharge order count:%s' % len(recharge_list))
    for tid, bg in recharge_list:
        bg.status = BudgetLog.CANCELED
        bg.save(update_fields=['status'])

