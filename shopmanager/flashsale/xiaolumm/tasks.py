#-*- encoding:utf8 -*-
import time
import datetime
from django.conf import settings
from celery.task import task

from flashsale.xiaolumm.models import Clicks,XiaoluMama

__author__ = 'meixqhi'



@task()
def task_Create_Click_Record(customer_id,openid):
    
    today = datetime.datetime.now()
    tf = datetime.datetime(today.year,today.month,today.day,0,0,0)
    tt = datetime.datetime(today.year,today.month,today.day,23,59,59)
    
    isvalid = False
    clicks = Clicks.objects.filter(openid=openid,created__gt=tf,created__lt=tt)
    click_count = len(clicks.values('linkid').distinct())
    xlmms = XiaoluMama.objects.filter(id=customer_id)
    
    if click_count <= Clicks.CLICK_DAY_LIMIT and xlmms.count() > 0:
        isvalid = True
        
    Clicks.objects.create(linkid=customer_id,openid=openid,isvalid=isvalid)


