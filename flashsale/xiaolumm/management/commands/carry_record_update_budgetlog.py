# coding=utf-8
from django.core.management.base import BaseCommand

from flashsale.pay.models import BudgetLog
from flashsale.xiaolumm.models.models_fortune import CarryRecord


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        根据carryrecord更新budgetlog
        """
        carry = CarryRecord.objects.filter(id=9637662).first()
        customer = carry.mama.get_mama_customer()
        budget_log_type = CarryRecord.budget_log_type_map(carry.carry_type)
        budget_log_status = CarryRecord.budget_log_status_map(carry.status)

        referal_id = 'carryrecord-%s' % carry.id
        bg = BudgetLog.objects.filter(referal_id=referal_id).first()
        if bg:
            bg.confirm_budget_log()
        else:
            if carry.carry_num > 0:
                BudgetLog.create(customer.id, BudgetLog.BUDGET_IN, carry.carry_num, budget_log_type,
                                 status=budget_log_status,
                                 referal_id=referal_id)

        carry = CarryRecord.objects.filter(id=9637663).first()
        customer = carry.mama.get_mama_customer()
        budget_log_type = CarryRecord.budget_log_type_map(carry.carry_type)
        budget_log_status = CarryRecord.budget_log_status_map(carry.status)

        referal_id = 'carryrecord-%s' % carry.id
        bg = BudgetLog.objects.filter(referal_id=referal_id).first()
        if bg:
            bg.confirm_budget_log()
        else:
            if carry.carry_num > 0:
                BudgetLog.create(customer.id, BudgetLog.BUDGET_IN, carry.carry_num, budget_log_type,
                                 status=budget_log_status,
                                 referal_id=referal_id)