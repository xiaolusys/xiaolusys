# -*- encoding:utf8 -*-
import datetime
from django.db.models import F
from celery.task import task

from shopapp.weixin.models import WXOrder
from flashsale.clickrebeta.models import StatisticsShoppingByDay,StatisticsShopping
from flashsale.xiaolumm.models import CarryLog,XiaoluMama,AgencyLevel,Clicks

import logging

__author__ = 'yann'

logger = logging.getLogger('celery.handler')


@task()
def task_Calc_Unstat_Order_Cash(target_date):
    """ 将点击跨过一天的未计算提成订单 提成金额更新至每日提成金额 """
    carry_no = int(target_date.strftime('%y%m%d'))
    
    time_from = datetime.datetime(target_date.year,target_date.month,target_date.day,0,0,0)
    time_to   = datetime.datetime(target_date.year,target_date.month,target_date.day,23,59,59)
    
    unstat_shop = StatisticsShopping.objects.filter(shoptime__range=(time_from,time_to),linkid=0)
    for mm_stat in unstat_shop:
        order_time = mm_stat.shoptime
        order_stat_from = order_time - datetime.timedelta(days=1)
        clicks = Clicks.objects.filter(click_time__range=(order_stat_from, order_time)).filter(
                                                openid=mm_stat.openid).order_by('-created')
        if clicks.count() == 0:
            continue
        
        click = clicks[0]
        mm_linkid = click.linkid

        xlmms = XiaoluMama.objects.filter(id=mm_linkid)
        if xlmms.count() == 0:
            continue
        
        xlmm = xlmms[0]
        agency_levels = AgencyLevel.objects.filter(id=xlmm.agencylevel)
        if agency_levels.count() == 0:
            continue
        agency_level = agency_levels[0]
        rebeta_rate  = agency_level.get_Rebeta_Rate()
        order_rebeta = mm_stat.wxorderamount * rebeta_rate
        if order_rebeta <= 0:
            continue
        
        stat_shop,state     = StatisticsShoppingByDay.objects.get_or_create(linkid=mm_linkid,tongjidate=target_date)
        stat_shop.linkname         = xlmm.weikefu
        stat_shop.ordernumcount    = F('ordernumcount') + 1
        stat_shop.orderamountcount = F('orderamountcount') + mm_stat.wxorderamount
        stat_shop.todayamountcount = F('todayamountcount') + mm_stat.wxorderamount
        stat_shop.save()
        
        c_log,state = CarryLog.objects.get_or_create(xlmm=mm_linkid,
                                                     order_num=carry_no,
                                                     log_type=CarryLog.ORDER_REBETA)

        c_log.value = F('value') + order_rebeta
        c_log.save()
        
        if c_log.status == CarryLog.CONFIRMED:
            XiaoluMama.objects.filter(id=mm_linkid).update(cash=F('cash') + order_rebeta)
        
        elif c_log.status == CarryLog.PENDING:
            XiaoluMama.objects.filter(id=mm_linkid).update(pending=F('pending') + order_rebeta)
        
        mm_stat.tichengcount = mm_stat.wxorderamount
        mm_stat.linkid = mm_linkid
        mm_stat.save()


@task()
def task_Push_Rebeta_To_MamaCash(target_date):
    
    carry_no = int(target_date.strftime('%y%m%d'))
    
    stat_by_days = StatisticsShoppingByDay.objects.filter(tongjidate=target_date)
    for mm_stat in stat_by_days:
        xlmms = XiaoluMama.objects.filter(id=mm_stat.linkid)
        if xlmms.count() == 0:
            continue
        
        xlmm = xlmms[0]
        agency_levels = AgencyLevel.objects.filter(id=xlmm.agencylevel)
        if agency_levels.count() == 0:
            continue
        agency_level = agency_levels[0]
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
    
    
    