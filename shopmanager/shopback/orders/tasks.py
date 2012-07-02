import os
import time
import datetime
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback.orders.models import Order,Trade,TradeExtraInfo,ORDER_FINISH_STATUS
from shopback.users.models import User
from auth.utils import format_time,format_datetime,format_year_month,parse_datetime
from auth.apis.exceptions import RemoteConnectionException,AppCallLimitedException,UserFenxiaoUnuseException,\
    APIConnectionTimeOutException,ServiceRejectionException
from auth import apis

import logging

logger = logging.getLogger('orders.handler')
BLANK_CHAR = ''
MONTH_TRADE_FILE_TEMPLATE = 'trade-month-%s.xls'



@task(max_retry=3)
def saveUserDuringOrders(user_id,days=0,update_from=None,update_to=None):

    if not(update_from and update_to):
        dt = datetime.datetime.now()
        if days >0 :
            update_from = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0)
                                     -datetime.timedelta(days,0,0))
            update_to   = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0))
        else:
            update_from = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0))
            update_to   = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,dt.hour,59,59)
                                     -datetime.timedelta(0,3600,0))

    has_next = True
    cur_page = 1
    error_times = 0
    #error_dict  = {'error_times':0}

    while has_next:
        try:
            response_list = apis.taobao_trades_sold_get(tb_user_id=user_id,page_no=cur_page
                ,page_size=settings.TAOBAO_PAGE_SIZE,use_has_next='true',start_created=update_from,end_created=update_to)

            order_list = response_list['trades_sold_get_response']
            if order_list.has_key('trades'):
                for trade in order_list['trades']['trade']:

                    Trade.save_trade_through_dict(user_id,trade)

            has_next = order_list['has_next']
            cur_page += 1
            error_times = 0
            time.sleep(settings.API_REQUEST_INTERVAL_TIME)
        except RemoteConnectionException,e:
            if error_times > settings.MAX_REQUEST_ERROR_TIMES:
                logger.error('update trade during order fail:%s ,repeat times:%d'%(response_list,error_times))
                raise e
            error_times += 1
        except APIConnectionTimeOutException,e:
            if error_times > settings.MAX_REQUEST_ERROR_TIMES:
                logger.error('update trade during order fail:%s ,repeat times:%d'%(response_list,error_times))
                raise e
            error_times += 1
            time.sleep(settings.API_TIME_OUT_SLEEP)
        except ServiceRejectionException,e:
            if error_times > settings.MAX_REQUEST_ERROR_TIMES:
                logger.error('update trade during order fail:%s ,repeat times:%d'%(response_list,error_times))
                raise e
            error_times += 1
            time.sleep(settings.API_OVER_LIMIT_SLEEP)
        except AppCallLimitedException,e:
            logger.error('update trade during order task fail',exc_info=True)
            raise e




@task()
def updateAllUserDuringOrders(days=0,update_from=None,update_to=None):

    hander_update  = update_from and update_to
    if hander_update:
        update_from = format_datetime(update_from)
        update_to   = format_datetime(update_to)

    users = User.objects.all()

    for user in users:
        if hander_update:
            saveUserDuringOrders(user.visitor_id,update_from=update_from,update_to=update_to)
        else:
            subtask(saveUserDuringOrders).delay(user.visitor_id,days=days)




@task(max_retry=3)
def saveUserDailyIncrementOrders(user_id,year=None,month=None,day=None):

    if year and month and day:
        s_dt_f = format_datetime(datetime.datetime(year,month,day,0,0,0))
        s_dt_t = format_datetime(datetime.datetime(year,month,day,23,59,59))
    else:
        dt = datetime.datetime.now()
        s_dt_f = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0)-datetime.timedelta(1,0,0))
        s_dt_t = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,23,59,59)-datetime.timedelta(1,0,0))

    has_next = True
    cur_page = 1
    error_times = 0

    while has_next:
        try:
            response_list = apis.taobao_trades_sold_increment_get(tb_user_id=user_id,page_no=cur_page
                ,page_size=settings.TAOBAO_PAGE_SIZE,use_has_next='true',start_modified=s_dt_f,end_modified=s_dt_t)

            trade_list = response_list['trades_sold_increment_get_response']
            if trade_list.has_key('trades'):
                for trade in trade_list['trades']['trade']:

                    Trade.save_trade_through_dict(user_id,trade)

            has_next = trade_list['has_next']
            cur_page += 1
            error_times = 0
            time.sleep(settings.API_REQUEST_INTERVAL_TIME)

        except RemoteConnectionException,e:
            if error_times > settings.MAX_REQUEST_ERROR_TIMES:
                logger.error('update trade during order fail:%s ,repeat times:%d'%(response_list,error_times))
                raise e
            error_times += 1
        except APIConnectionTimeOutException,e:
            if error_times > settings.MAX_REQUEST_ERROR_TIMES:
                logger.error('update trade during order fail:%s ,repeat times:%d'%(response_list,error_times))
                raise e
            error_times += 1
            time.sleep(settings.API_TIME_OUT_SLEEP)
        except ServiceRejectionException,e:
            if error_times > settings.MAX_REQUEST_ERROR_TIMES:
                logger.error('update trade during order fail:%s ,repeat times:%d'%(response_list,error_times))
                raise e
            error_times += 1
            time.sleep(settings.API_OVER_LIMIT_SLEEP)
        except AppCallLimitedException,e:
            logger.error('update trade sold increment fail',exc_info=True)
            raise e





@task()
def updateAllUserDailyIncrementOrders(update_from=None,update_to=None):

    hander_update = update_from and update_to
    if hander_update:
        time_delta = update_to - update_from
        update_days  = time_delta.days+1

    users = User.objects.all()
    for user in users:
        if hander_update:
            for i in xrange(0,update_days):
                update_date = update_to - datetime.timedelta(i,0,0)
                saveUserDailyIncrementOrders(
                        user.visitor_id,year=update_date.year,month=update_date.month,day=update_date.day)
        else:
            subtask(saveUserDailyIncrementOrders).delay(user.visitor_id)




@task()
def updateOrdersAmountTask(user_id,update_from=None,update_to=None):

    finish_trades = Trade.objects.filter(seller_id=user_id,consign_time__gte=update_from,
                                         consign_time__lte=update_to,status=ORDER_FINISH_STATUS)

    error_times = 0

    for trade in finish_trades:
        trade_extra_info,state = TradeExtraInfo.objects.get_or_create(tid=trade.id)

        if trade_extra_info.is_update_amount:
            continue

        try:
            response_list = apis.taobao_trade_amount_get(tid=trade.id,tb_user_id=user_id)

            tamt = response_list['trade_amount_get_response']['trade_amount']
            trade.cod_fee = tamt['cod_fee']
            trade.total_fee = tamt['total_fee']
            trade.post_fee = tamt['post_fee']
            trade.commission_fee = tamt['commission_fee']
            trade.buyer_obtain_point_fee  = tamt['buyer_obtain_point_fee']
            trade.pay_time = parse_datetime(tamt['pay_time'])
            trade.is_update_amount = True
            trade.save()

            trade_extra_info.is_update_amount = True
            trade_extra_info.save()

            for o in tamt['order_amounts']['order_amount']:
                try:
                    order = Order.objects.get(oid=o['oid'])
                    order.discount_fee = o['discount_fee']
                    order.adjust_fee   = o['adjust_fee']
                    order.payment      = o['payment']
                    order.price        = o['price']
                    order.num          = o['num']
                    order.num_iid      = o['num_iid']
                    order.save()
                except Order.DoesNotExist:
                    logger.error('the order(id:%s) does not exist'%o['oid'])

            error_times = 0
            time.sleep(settings.API_REQUEST_INTERVAL_TIME)

        except RemoteConnectionException,e:
            if error_times > settings.MAX_REQUEST_ERROR_TIMES:
                logger.error('update trade during order fail:%s ,repeat times:%d'%(response_list,error_times))
                raise e
            error_times += 1
        except APIConnectionTimeOutException,e:
            if error_times > settings.MAX_REQUEST_ERROR_TIMES:
                logger.error('update trade during order fail:%s ,repeat times:%d'%(response_list,error_times))
                raise e
            error_times += 1
            time.sleep(settings.API_TIME_OUT_SLEEP)
        except ServiceRejectionException,e:
            if error_times > settings.MAX_REQUEST_ERROR_TIMES:
                logger.error('update trade during order fail:%s ,repeat times:%d'%(response_list,error_times))
                raise e
            error_times += 1
            time.sleep(settings.API_OVER_LIMIT_SLEEP)
        except AppCallLimitedException,e:
            logger.error('%s'%exc,exc_info=True)
            raise e




@task()
def updateAllUserOrdersAmountTask(days=0,dt_f=None,dt_t=None):

    hander_update = dt_f and dt_t
    if not hander_update:
        dt = datetime.datetime.now()
        dt_f = datetime.datetime(dt.year,dt.month,dt.day,0,0,0)\
            - datetime.timedelta(days,0,0)
        dt_t = datetime.datetime(dt.year,dt.month,dt.day,23,59,59)\
            - datetime.timedelta(1,0,0)

    users = User.objects.all()
    for user in users:
        if hander_update:
            updateOrdersAmountTask(user.visitor_id,update_from=dt_f,update_to=dt_t)
        else:
            subtask(updateOrdersAmountTask).delay(user.visitor_id,update_from=dt_f,update_to=dt_t)











