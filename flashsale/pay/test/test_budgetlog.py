# encoding=utf8
import os
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shopmanager.local_settings')
import django
django.setup()
from flashsale.pay.models import BudgetLog
from flashsale.pay.models.user import UserBudget

if __name__ == '__main__':

    customer_id = 58
    budget = UserBudget.objects.filter(user_id=customer_id).first()
    # budget.save()
    # if budget:
    #     print '>>> before:', budget
    #
    # bg = BudgetLog.create(customer_id, BudgetLog.BUDGET_IN, 10, BudgetLog.BG_SUBSCRIBE)
    bg = BudgetLog.objects.get(id=1)
    bg.save()
    # bg = BudgetLog.create(customer_id, BudgetLog.BUDGET_OUT, 10, BudgetLog.BG_SUBSCRIBE)
    # print '>>> budgetlog:', bg
    #
    # budget = UserBudget.objects.get(user_id=customer_id)
    # print '>>> after:', budget

