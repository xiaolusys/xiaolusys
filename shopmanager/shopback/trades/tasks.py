#-*- coding:utf8 -*-
import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback import paramconfig as pcfg
from shopback.trades.models import MergeTrade,MergeBuyerTrade
from shopback.users.models import User
from auth import apis
import logging

logger = logging.getLogger('trades.handler')

       
@task()
def regularRemainOrderTask():
    #更新定时提醒订单
    dt = datetime.datetime.now()
    dt = datetime.datetime(dt.year,dt.month,dt.day,0,0,0)
    MergeTrade.objects.filter(sys_status=pcfg.REGULAR_REMAIN_STATUS,remind_time__lte=dt).update(sys_status=pcfg.WAIT_AUDIT_STATUS)

    

