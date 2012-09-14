#-*- coding:utf8 -*-
import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from auth.utils import format_time,format_datetime,format_year_month,parse_datetime
from shopback.fenxiao.models import PurchaseOrder,FenxiaoProduct,SubPurchaseOrder
from shopback.trades.models import WAIT_SELLER_SEND_GOODS 
from auth.apis.exceptions import UserFenxiaoUnuseException,TaobaoRequestException
from shopback.monitor.models import TradeExtraInfo,SystemConfig,DayMonitorStatus
from shopback.users.models import User
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
        logger.warn('the current user(id:%s)is not fenxiao platform user,error:%s'%(str(user_id),exc))
    except TaobaoRequestException,exc:
        logger.error('%s'%exc,exc_info=True)


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
            
            if not (dt_f and dt_t):
                dt_t = datetime.datetime.now()
                dt_f = dt_t - datetime.timedelta(7,0,0)
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
        logger.warn("the current user (id:%s) is not fenxiao platform user,error:%s"%(str(user_id),exc))
    except TaobaoRequestException,exc:
        logger.error('%s'%exc,exc_info=True)

        


@task()
def updateAllUserPurchaseOrderTask(update_from=None,update_to=None,status=None):

    users = User.objects.all()
    for user in users:

        saveUserPurchaseOrderTask(user.visitor_id,update_from=update_from,update_to=update_to,status=status)

            
  
  
  
@task()
def saveUserIncrementPurchaseOrderTask(user_id,update_from=None,update_to=None):
    try:           
        update_from = format_datetime(update_from)
        update_to   = format_datetime(update_to)
    
        has_next = True
        cur_page = 1
        
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

    except UserFenxiaoUnuseException,exc:
        logger.warn("the current user(id:%s) is not fenxiao platform user,error:%s"%(str(user_id),exc))

    
@task()
def updateAllUserIncrementPurchaseOrderTask(update_from=None,update_to=None):
    
    update_handler = update_from and update_to
    dt   = datetime.datetime.now()
    
    if update_handler:
        time_delta = update_to - update_from
        update_days  = time_delta.days+1
    else:
        update_to   = datetime.datetime(dt.year,dt.month,dt.day,0,0,0)
        update_days = 1
        
    users = User.objects.all()
    
    for user in users:
        for i in xrange(0,update_days):
            update_start = update_to - datetime.timedelta(i+1,0,0)
            update_end   = update_to - datetime.timedelta(i,0,0)
            
            year  = update_start.year
            month = update_start.month
            day   = update_start.day
             
            monitor_status,state = DayMonitorStatus.objects.get_or_create(user_id=user.visitor_id,year=year,month=month,day=day)
            try:
               if not monitor_status.update_purchase_increment: 
                   saveUserIncrementPurchaseOrderTask(user.visitor_id,update_from=update_start,update_to=update_end)
            except Exception,exc:
                logger.error('%s'%exc,exc_info=True)
            else:
                monitor_status.update_purchase_increment = True
                monitor_status.save()

   
  
@apis.single_instance_task(60*60,prefix='shopback.fenxiao.tasks.')
def updateAllUserIncrementPurchasesTask():
    """ 增量更新分销平台订单信息 """
    
    dt = datetime.datetime.now()
    sysconf = SystemConfig.getconfig()
    users   = User.objects.all()
    updated = sysconf.fenxiao_order_updated 
    try:
        if updated:
            bt_dt = dt-updated
            if bt_dt.days>=1:
                for user in users:
                    saveUserPurchaseOrderTask(user.visitor_id,status=WAIT_SELLER_SEND_GOODS)
            else:
                for user in users:
                    saveUserIncrementPurchaseOrderTask(user.visitor_id,update_from=updated,update_to=dt)
        else:
            for user in users:
                saveUserPurchaseOrderTask(user.visitor_id,status=WAIT_SELLER_SEND_GOODS)
    except Exception,exc:
        logger.error('%s'%exc,exc_info=True)
    else:
        SystemConfig.objects.filter(id=sysconf.id).update(fenxiao_order_updated=dt)  
