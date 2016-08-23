#!/usr/bin/env python
import os
import sys
from global_setup import setup_djagno_environ
setup_djagno_environ()
import django
django.setup()
import datetime
from flashsale.xiaolumm.tasks_mama_carry_total import *
from flashsale.xiaolumm.tasks_mama import *
from flashsale.pay.models import SaleOrder

if __name__ == '__main__':
    print 'helloworld'
    print datetime.datetime.now()
    # task_schedule_update_carry_total_ranking.delay(countdown=10)
    # task_schedule_update_carry_total_ranking.apply_async(countdown=10)
    instance = SaleOrder.objects.exclude(pay_time=None).order_by('-id')[5]
    # task_order_trigger.apply_async(instance)
    task_order_trigger.apply_async(args=[instance], countdown=1)