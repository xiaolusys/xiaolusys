# -*- encoding:utf8 -*-
import time
import datetime
import calendar
from django.conf import settings
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopapp.weixin.models import WXOrder
from flashsale.clickrebeta.models import StatisticsShoppingByDay,StatisticsShopping


import logging

__author__ = 'yann'

logger = logging.getLogger('celery.handler')


@task(max_retry=3, default_retry_delay=5)
def task_Tongji_User_Order(pre_day=1):
    try:

        yesterday = datetime.date.today() - datetime.timedelta(days=pre_day)
        time_from = datetime.datetime(yesterday.year, yesterday.month, yesterday.day)
        time_to = datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)

        wxorders = WXOrder.objects.filter(order_create_time__range=(time_from,time_to))
        tongjibyday = StatisticsShoppingByDay.objects.filter(tongjidate__range=(time_from,time_to))
        tongjibyday.delete()
        for wxorder in wxorders:
            wxorder.confirm_payment()

    except Exception, exc:
        raise task_Tongji_User_Order.retry(exc=exc)


@task(max_retry=3, default_retry_delay=5)
def task_Tongji_All_Order():
    try:
        StatisticsShoppingByDay.objects.all().delete()
        StatisticsShopping.objects.all().delete()
        all = WXOrder.objects.all()
        cnt = 0
        for order1 in all:
            order1.confirm_payment()
            cnt += 1
            if cnt % 1000 == 0:
                print cnt
    
    except Exception, exc:
        raise task_Tongji_All_Order.retry(exc=exc)
    
    
    