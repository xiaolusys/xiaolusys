#-*- coding:utf8 -*-
import os
import time
import datetime
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback.orders.models import Order,Trade
from shopback.users.models import User
from shopback.monitor.models import TradeExtraInfo
from shopback.monitor.models import DayMonitorStatus
from auth.utils import format_time,format_datetime,format_year_month,parse_datetime
from auth.apis.exceptions import RemoteConnectionException,AppCallLimitedException,UserFenxiaoUnuseException,\
    APIConnectionTimeOutException,ServiceRejectionException
from auth import apis

import logging

logger = logging.getLogger('orders.handler')
BLANK_CHAR = ''




@task(max_retry=3)
def saveUserDuringOrdersTask(user_id,update_from=None,update_to=None,status=None):
            
    update_from = format_datetime(update_from) if update_from else None
    update_to   = format_datetime(update_to) if update_to else None
    
    has_next = True
    cur_page = 1

    while has_next:
    
        response_list = apis.taobao_trades_sold_get(tb_user_id=user_id,page_no=cur_page,use_has_next='true',fields='tid,modified'
            ,page_size=settings.TAOBAO_PAGE_SIZE,start_created=update_from,end_created=update_to,status=status)

        order_list = response_list['trades_sold_get_response']
        if order_list.has_key('trades'):
            for trade in order_list['trades']['trade']:
                modified = parse_datetime(trade['modified']) if trade.get('modified',None) else None
                trade_obj,state = Trade.objects.get_or_create(pk=trade['tid'])
                if trade_obj.modified != modified:
                    try:
                        response = apis.taobao_trade_fullinfo_get(tid=trade['tid'],tb_user_id=user_id)
                        trade_dict = response['trade_fullinfo_get_response']['trade']
                        Trade.save_trade_through_dict(user_id,trade_dict)
                    except Exception,exc:
                        logger.error('update trade fullinfo error:%s'%exc,exc_info=True)

        has_next = order_list['has_next']
        cur_page += 1





@task()
def updateAllUserDuringOrdersTask(update_from=None,update_to=None,status=None):


    users = User.objects.all()

    for user in users:
        
        saveUserDuringOrdersTask(user.visitor_id,update_from=update_from,update_to=update_to,status=status)
   




@task()
def saveUserIncrementOrdersTask(user_id,year=None,month=None,day=None):
    
    if not(year and month and day):
        dt    = datetime.datetime.now()-datetime.timedelta(1,0,0)
        year  = dt.year
        month = dt.month
        day   = dt.day
        
    s_dt_f = format_datetime(datetime.datetime(year,month,day,0,0,0))
    s_dt_t = format_datetime(datetime.datetime(year,month,day,23,59,59))

    has_next = True
    cur_page = 1
    
    day_monitor_status,state = DayMonitorStatus.objects.get_or_create(user_id=user_id,year=year,month=month,day=day)
    while has_next:
       
        response_list = apis.taobao_trades_sold_increment_get(tb_user_id=user_id,page_no=cur_page,fields='tid,modified'
            ,page_size=settings.TAOBAO_PAGE_SIZE,use_has_next='true',start_modified=s_dt_f,end_modified=s_dt_t)

        trade_list = response_list['trades_sold_increment_get_response']
        if trade_list.has_key('trades'):
            for trade in trade_list['trades']['trade']:
                modified = parse_datetime(trade['modified']) if trade.get('modified',None) else None
                trade_obj,state = Trade.objects.get_or_create(pk=trade['tid'])
                if trade_obj.modified != modified:
                    try:
                        response = apis.taobao_trade_fullinfo_get(tid=trade['tid'],tb_user_id=user_id)
                        trade_dict = response['trade_fullinfo_get_response']['trade']
                        Trade.save_trade_through_dict(user_id,trade_dict)
                    except Exception,exc:
                        logger.error('update trade fullinfo error：%s'%exc,exc_info=True)

        has_next = trade_list['has_next']
        cur_page += 1
        
    day_monitor_status.update_trade_increment = True
    day_monitor_status.save()




@task()
def updateAllUserIncrementOrdersTask(update_from=None,update_to=None):

    hander_update = update_from and update_to
    if hander_update:
        time_delta = update_to - update_from
        update_days  = time_delta.days+1

    users = User.objects.all()
    for user in users:
        if hander_update:
            for i in xrange(0,update_days):
                update_date = update_to - datetime.timedelta(i,0,0)
                saveUserIncrementOrdersTask(
                        user.visitor_id,year=update_date.year,month=update_date.month,day=update_date.day)
        else:
            subtask(saveUserIncrementOrdersTask).delay(user.visitor_id)














