# -*- encoding:utf8 -*-
import datetime
from django.db.models import F
from celery.task import task

from shopapp.weixin.models import WXOrder
from flashsale.clickrebeta.models import StatisticsShoppingByDay,StatisticsShopping
from flashsale.xiaolumm.models import CarryLog,XiaoluMama,AgencyLevel

import logging

__author__ = 'yann'

logger = logging.getLogger('celery.handler')


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
def task_Push_Pending_Carry_Cash(day_ago=7):
    
    pre_date = datetime.date.today() - datetime.timedelta(days=day_ago)
    
    c_logs = CarryLog.objects.filter(carry_date__lt=pre_date,status=CarryLog.PENDING)
    for cl in c_logs:
        #重新计算pre_date之前订单金额，取消退款订单提成
        
        #将carrylog里的金额更新到最新，然后将金额写入mm的钱包帐户
        xlmms = XiaoluMama.objects.filter(id=cl.xlmm)
        if cl.carry_type != CarryLog.CARRY_IN:
            continue
        
        urows = xlmms.update(cash=F('cash') + cl.value, pending=F('pending') - cl.value)
        if urows > 0:
            cl.status = CarryLog.CONFIRMED
            cl.save()
        
        

@task()
def task_Push_Rebeta_To_MamaCash(target_date):
    
    carry_no = int(target_date.strftime('%y%m%d'))
    
    stat_by_days = StatisticsShoppingByDay.objects.filter(tongjidate=target_date)
    for mm_stat in stat_by_days:
        xlmms = XiaoluMama.objects.filter(id=mm_stat.linkid)
        if xlmms.count() == 0:
            continue
        
        xlmm = xlmms[0]
        agency_level = AgencyLevel.objects.get(id=xlmm.agencylevel)
        rebeta_rate  = agency_level.get_Rebeta_Rate()
        order_rebeta = mm_stat.todayamountcount * rebeta_rate
        if order_rebeta <= 0:
            continue
        
        c_log,state = CarryLog.objects.get_or_create(xlmm=xlmm.id,
                                                     order_num=carry_no,
                                                     log_type=CarryLog.ORDER_REBETA)
        if not state :
            continue
        c_log.value  = order_rebeta
        c_log.carry_date = target_date
        c_log.carry_type = CarryLog.CARRY_IN
        c_log.status = CarryLog.PENDING
        c_log.save()
        
        urows = XiaoluMama.objects.filter(id=mm_stat.linkid).update(pending=F('pending') + order_rebeta)
        if urows == 0:
            raise Exception(u'小鹿妈妈订单提成返现更新异常:%s,%s'%(xlmm.id,urows))
        

@task(max_retry=3, default_retry_delay=5)
def task_Tongji_User_Order(pre_day=1):
    try:

        pre_date  = datetime.date.today() - datetime.timedelta(days=pre_day)
        time_from = datetime.datetime(pre_date.year, pre_date.month, pre_date.day)
        time_to = datetime.datetime(pre_date.year, pre_date.month, pre_date.day, 23, 59, 59)

        wxorders = WXOrder.objects.filter(order_create_time__range=(time_from,time_to))
        stat_shoppings = StatisticsShopping.objects.filter(shoptime__range=(time_from,time_to))
        stat_shoppings.delete()
        
        tongjibyday = StatisticsShoppingByDay.objects.filter(tongjidate__range=(time_from,time_to))
        tongjibyday.delete()
        
        for wxorder in wxorders:
            wxorder.confirm_payment()
        
        #update xlmm Cash
        task_Push_Rebeta_To_MamaCash(pre_date)
        
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
    
    
    