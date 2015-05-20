#-*- encoding:utf8 -*-
import time
import datetime
from django.db.models import F
from django.conf import settings
from celery.task import task

from flashsale.xiaolumm.models import Clicks,XiaoluMama,CarryLog

__author__ = 'meixqhi'

@task()
def task_Create_Click_Record(xlmmid,openid):
    
    today = datetime.datetime.now()
    tf = datetime.datetime(today.year,today.month,today.day,0,0,0)
    tt = datetime.datetime(today.year,today.month,today.day,23,59,59)
    
    isvalid = False
    clicks = Clicks.objects.filter(openid=openid,created__gt=tf,created__lt=tt)
    click_linkids = set([l.get('linkid') for l in clicks.values('linkid').distinct()])
    click_count   = len(click_linkids)
    xlmms = XiaoluMama.objects.filter(id=xlmmid)
    
    if click_count < Clicks.CLICK_DAY_LIMIT and xlmms.count() > 0 and xlmmid not in click_linkids:
        isvalid = True
        
    Clicks.objects.create(linkid=xlmmid,openid=openid,isvalid=isvalid)
    
    
@task()
def task_Pull_Pending_Carry(day_ago=7):
    
    date_to  = datetime.datetime.now().date()
    date_from    = date_to - datetime.timedelta(days=day_ago)
    
    c_logs = CarryLog.objects.filter(carry_date__range=(date_from,date_to),
                                     log_type__in=(CarryLog.ORDER_REBETA,),#CarryLog.CLICK_REBETA
                                     status=CarryLog.CONFIRMED)

    for cl in c_logs:
        #重新计算pre_date之前订单金额，取消退款订单提成
        
        #将carrylog里的金额更新到最新，然后将金额写入mm的钱包帐户
        xlmms = XiaoluMama.objects.filter(id=cl.xlmm)
        
        if cl.carry_date == datetime.datetime(2015,5,15).date():
            urows = xlmms.update(cash=F('cash') - cl.value)
        else:
            urows = xlmms.update(pending=F('pending') - cl.value)
        
        if urows > 0:
            cl.status = CarryLog.PENDING
            cl.save()

@task()
def task_Push_Pending_Carry_Cash(day_ago=7, xlmm_id=None):
    
    from flashsale.mmexam.models import Result
    
    pre_date = datetime.date.today() - datetime.timedelta(days=day_ago)
    
    c_logs = CarryLog.objects.filter(log_type__in=(CarryLog.ORDER_REBETA,
                                                   CarryLog.CLICK_REBETA), 
                                     status=CarryLog.PENDING)\
                                     .exclude(carry_date__gt=pre_date,log_type=CarryLog.ORDER_REBETA)
    
    if xlmm_id:
        xlmm  = XiaoluMama.objects.get(id=xlmm_id)
        c_logs = c_logs.filter(xlmm=xlmm.id)
        
    for cl in c_logs:
        
        xlmms = XiaoluMama.objects.filter(id=cl.xlmm)
        if xlmms.count() == 0:
            continue
        
        xlmm = xlmms[0]
        #是否考试通过
        results = Result.objects.filter(daili_user=xlmm.openid)
        if results.count() == 0 or not results[0].is_Exam_Funished():
            continue
        #重新计算pre_date之前订单金额，取消退款订单提成
        
        #将carrylog里的金额更新到最新，然后将金额写入mm的钱包帐户
        
        if cl.carry_type != CarryLog.CARRY_IN:
            continue
        
        urows = xlmms.update(cash=F('cash') + cl.value, pending=F('pending') - cl.value)
        if urows > 0:
            cl.status = CarryLog.CONFIRMED
            cl.save()
            
            
    
    


