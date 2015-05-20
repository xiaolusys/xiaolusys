# -*- encoding:utf8 -*-
import datetime
from django.db.models import F,Sum
from celery.task import task

from flashsale.clickcount.models import ClickCount
from flashsale.clickrebeta.models import StatisticsShopping
from flashsale.xiaolumm.models import Clicks
from flashsale.pay.models import Customer
from .models import DailyStat

import logging

__author__ = 'yann'

logger = logging.getLogger('celery.handler')

@task()
def task_Push_Sales_To_DailyStat(target_date):
    
    df = datetime.datetime(target_date.year,target_date.month,target_date.day,0,0,0)
    dt = datetime.datetime(target_date.year,target_date.month,target_date.day,23,59,59)
    
    seven_day_ago = target_date - datetime.timedelta(days=7)
    seven_day_before = datetime.datetime(seven_day_ago.year,seven_day_ago.month,seven_day_ago.day,0,0,0)
#     click_count = ClickCount.objects.get(date=target_date)
#     cc_stats = click_count.aggregate(total_user_num=Sum('user_num'),
#                                      total_valid_num=Sum('valid_num'))
    clicks = Clicks.objects.filter(created__range=(df,dt))
    
    total_click_count = clicks.values('linkid','openid').distinct().count()
    total_user_num  = clicks.values('openid').distinct().count()
    total_valid_count = clicks.filter(isvalid=True).values('linkid','openid').distinct().count()
    
    total_old_visiter_num = 0
    click_openids = clicks.values('openid').distinct()
    for stat in click_openids:
        last_clicks = Clicks.objects.filter(created__lte=df,openid=stat['openid'])
        if last_clicks.count() > 0:
            total_old_visiter_num += 1
    
    shoping_stats     = StatisticsShopping.objects.filter(shoptime__range=(df,dt))
    total_payment     = shoping_stats.aggregate(total_payment=Sum('tichengcount')).get('total_payment') or 0
    total_order_num   = shoping_stats.values('wxorderid').distinct().count()
    total_buyer_num   = shoping_stats.values('openid').distinct().count()
    
    total_old_buyer_num = 0
    seven_old_buyer_num = 0
    
    total_old_order_num = 0
    stats_openids = shoping_stats.values('openid').distinct()
    for stat in stats_openids:
        day_ago_stats = StatisticsShopping.objects.filter(shoptime__lte=df,openid=stat['openid'])
        if day_ago_stats.count() > 0:
            total_old_buyer_num += 1
            total_old_order_num += shoping_stats.filter(openid=stat['openid']).values('wxorderid').distinct().count()
        
        seven_day_ago_stats = StatisticsShopping.objects.filter(shoptime__lte=seven_day_before,
                                                                openid=stat['openid'])
        if seven_day_ago_stats.count() > 0:
            seven_old_buyer_num += 1
            
    dstat, state = DailyStat.objects.get_or_create(day_date=target_date)
    dstat.total_click_count = total_click_count
    dstat.total_valid_count = total_valid_count
    dstat.total_visiter_num = total_user_num
    dstat.total_new_visiter_num = total_user_num - total_old_visiter_num
    
    dstat.total_payment     = total_payment
    dstat.total_order_num   = total_order_num
    dstat.total_new_order_num   = total_order_num - total_old_order_num
    
    dstat.total_buyer_num   = total_buyer_num
    dstat.total_old_buyer_num   = total_old_buyer_num
    dstat.seven_buyer_num   = seven_old_buyer_num
    dstat.save()
    
@task()
def task_Calc_Sales_Stat_By_Day(pre_day=1):
    
    pre_date = datetime.date.today() - datetime.timedelta(days=pre_day)
    
    task_Push_Sales_To_DailyStat(pre_date)
    
    

    