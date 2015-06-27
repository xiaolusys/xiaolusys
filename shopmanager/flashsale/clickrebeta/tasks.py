# -*- encoding:utf8 -*-
import datetime
from django.db.models import F
from celery.task import task

from shopapp.weixin.models import WXOrder
from flashsale.pay.models import SaleTrade
from flashsale.clickrebeta.models import StatisticsShoppingByDay,StatisticsShopping
from flashsale.xiaolumm.models import CarryLog,XiaoluMama,AgencyLevel,Clicks

import logging

__author__ = 'yann'

logger = logging.getLogger('celery.handler')


@task()
def task_Push_Rebeta_To_MamaCash(target_date):
    
    carry_no = int(target_date.strftime('%y%m%d'))
    
    stat_by_days = StatisticsShoppingByDay.objects.filter(tongjidate=target_date)
    for mm_stat in stat_by_days:
        xlmms = XiaoluMama.objects.filter(id=mm_stat.linkid)
        if xlmms.count() == 0:
            continue
        
        xlmm = xlmms[0]
        rebeta_rate = xlmm.get_Mama_Order_Rebeta_Rate()
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
        
        XiaoluMama.objects.filter(id=mm_stat.linkid).update(pending=F('pending') + order_rebeta)
  
        

@task(max_retry=3, default_retry_delay=5)
def task_Tongji_User_Order(pre_day=1):
    try:

        pre_date  = datetime.date.today() - datetime.timedelta(days=pre_day)
        time_from = datetime.datetime(pre_date.year, pre_date.month, pre_date.day)
        time_to = datetime.datetime(pre_date.year, pre_date.month, pre_date.day, 23, 59, 59)

        wxorders = WXOrder.objects.filter(order_create_time__range=(time_from,time_to))
        saletrades   = SaleTrade.objects.filter(pay_time__range=(time_from,time_to))
        
        stat_shoppings = StatisticsShopping.objects.filter(shoptime__range=(time_from,time_to))
        stat_shoppings.delete()
        
        tongjibyday = StatisticsShoppingByDay.objects.filter(tongjidate__range=(time_from,time_to))
        tongjibyday.delete()
        
        for wxorder in wxorders:
            wxorder.confirm_payment()
            
        for strade in saletrades:
            strade.confirm_payment()
        
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
    
    
    