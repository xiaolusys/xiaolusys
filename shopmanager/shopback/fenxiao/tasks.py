#-*- coding:utf8 -*-
import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from auth.utils import format_time,format_datetime,format_year_month,parse_datetime
from shopback.fenxiao.models import PurchaseOrder,FenxiaoProduct,SubPurchaseOrder
from auth.apis.exceptions import RemoteConnectionException,AppCallLimitedException,UserFenxiaoUnuseException,\
    APIConnectionTimeOutException,ServiceRejectionException
from shopback.users.models import User
from shopback.monitor.models import DayMonitorStatus
from auth import apis
import logging
__author__ = 'meixqhi'

logger = logging.getLogger('fenxiao.handler')



@task()
def saveUserFenxiaoProductTask(user_id):
    try:
        has_next    = True
        cur_page    = 1
        
        while has_next:
    
            response_list = apis.taobao_fenxiao_products_get(page_no=cur_page,page_size=settings.TAOBAO_PAGE_SIZE/2
                        ,tb_user_id=user_id)
            products = response_list['fenxiao_products_get_response']
            if products['total_results']>0:
                fenxiao_product_list = products['products']['fenxiao_product']
                for fenxiao_product in fenxiao_product_list:
                    FenxiaoProduct.save_fenxiao_product_dict(user_id,fenxiao_product)
            
            total_nums = products['total_results']
            cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
            has_next = cur_nums<total_nums
            cur_page += 1
    
    except UserFenxiaoUnuseException,exc:
        logger.warn('当前用户(id:%s)不是分销平台用户'%str(user_id))



@task()
def updateAllUserFenxiaoProductTask():

    users = User.objects.all()
    for user in users:

        saveUserFenxiaoProductTask(user.visitor_id)
     


@task()
def saveUserPurchaseOrderTask(user_id,update_from=None,update_to=None,status=None):
    try:
        update_handler = update_from and update_to
        exec_times = (update_from - update_to).days/7+1 if update_handler else 1
        
        for i in range(0,exec_times):
            dt_f = update_from + datetime.timedelta(i*7,0,0) if update_handler else None
            dt_t = update_from + datetime.timedelta((i+1)*7,0,0) if update_handler else None
            has_next = True
            cur_page = 1
        
            while has_next:
        
                response_list = apis.taobao_fenxiao_orders_get(tb_user_id=user_id,page_no=cur_page,time_type='trade_time_type'
                    ,page_size=settings.TAOBAO_PAGE_SIZE/2,start_created=dt_f,end_created=dt_t,status=status)
        
                orders_list = response_list['fenxiao_orders_get_response']
                if orders_list['total_results']>0:
                    for o in orders_list['purchase_orders']['purchase_order']:
        
                        order,state = PurchaseOrder.objects.get_or_create(pk=o['fenxiao_id'])
                        order.save_order_through_dict(user_id,o)
        
                total_nums = orders_list['total_results']
                cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
                has_next = cur_nums<total_nums
                cur_page += 1

    except UserFenxiaoUnuseException,exc:
        logger.warn('当前用户（%s）未使用分销平台'%user_id)
 



@task()
def updateAllUserPurchaseOrderTask(update_from=None,update_to=None,status=None):

    hander_update  = update_from and update_to

    users = User.objects.all()
    for user in users:

        saveUserPurchaseOrderTask(user.visitor_id,update_from=dt_f,update_to=dt_t,status=status)

            
  
  
  
@task()
def saveUserIncrementPurchaseOrderTask(user_id,year=None,month=None,day=None):
    try:
        if not(year and month and day):
            last_day = datetime.datetime.now() - datetime.timedelta(1,0,0)
            year  = last_day.year
            month = last_day.month
            day   = last_day.day
                    
        update_from = format_datetime(datetime.datetime(year,month,day,0,0,0))
        update_to   = format_datetime(datetime.datetime(year,month,day,23,59,59))
    
        has_next = True
        cur_page = 1
        
        day_monitor_status,state = DayMonitorStatus.objects.get_or_create(user_id=user_id,year=year,month=month,day=day)
        
        while has_next:
    
            response_list = apis.taobao_fenxiao_orders_get(tb_user_id=user_id,page_no=cur_page,time_type='update_time_type'
                ,page_size=settings.TAOBAO_PAGE_SIZE/2,start_created=update_from,end_created=update_to)
    
            orders_list = response_list['fenxiao_orders_get_response']
            if orders_list['total_results']>0:
                for o in orders_list['purchase_orders']['purchase_order']:
    
                    order,state = PurchaseOrder.objects.get_or_create(pk=o['fenxiao_id'])
                    order.save_order_through_dict(user_id,o)
    
            total_nums = orders_list['total_results']
            cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
            has_next = cur_nums<total_nums
            cur_page += 1 
        
        day_monitor_status.update_purchase_increment = True
        day_monitor_status.save()
    
    except UserFenxiaoUnuseException,exc:
        logger.warn('当前用户（%s）未使用分销平台'%user_id)

    
    
    
@task()
def updateAllUserIncrementPurchaseOrderTask(update_from=None,update_to=None):

    hander_update  = update_from and update_to
    users = User.objects.all()
    
    for user in users:
        if hander_update:
            interval_date = update_to - update_from
            for i in xrange(0,interval_date.days+1):
                dt = update_from + datetime.timedelta(i,0,0)
                saveUserIncrementPurchaseOrderTask(user.visitor_id,year=dt.year,month=dt.month,day=dt.day)
        else:
            saveUserIncrementPurchaseOrderTask(user.visitor_id)    
  
  