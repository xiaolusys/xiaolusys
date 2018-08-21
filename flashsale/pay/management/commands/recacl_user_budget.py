# coding=utf-8
from django.core.management.base import BaseCommand

from flashsale.pay.tasks import task_budgetlog_update_userbudget

class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        根据customerid更新budgetlog
        """
        task_budgetlog_update_userbudget(498685)
        task_budgetlog_update_userbudget(1985079)
