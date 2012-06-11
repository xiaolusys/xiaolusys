import os
import time
import datetime
import calendar
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback.orders.models import Order,Trade,Logistics,PurchaseOrder,Refund,MonthTradeReportStatus,ORDER_FINISH_STATUS
from shopback.users.models import User
from auth.utils import format_time,format_datetime,format_year_month,parse_datetime,refresh_session
from shopback.orders.reportform import TradesToXLSFile
from auth.apis.exceptions import RemoteConnectionException,AppCallLimitedException,UserFenxiaoUnuseException,\
    APIConnectionTimeOutException,ServiceRejectionException
from auth import apis

import logging

logger = logging.getLogger('exception.handler')
BLANK_CHAR = ''
MONTH_TRADE_FILE_TEMPLATE = 'trade-month-%s.xls'



@task(max_retry=3)
def saveUserDuringOrders(user_id,days=0,update_from=None,update_to=None):
    try:
        user = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist,exc:
        logger.error('SaveUserDuringOrders error:%s'%exc, exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

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
    error_dict  = {'error_times':0}

    while has_next:
        try:
            response_list = apis.taobao_trades_sold_get(session=user.top_session,page_no=cur_page
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
    try:
        user = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist,exc:
        logger.error('saveUserDailyIncrementOrders error:%s'%exc, exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

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
            response_list = apis.taobao_trades_sold_increment_get(session=user.top_session,page_no=cur_page
                ,page_size=settings.TAOBAO_PAGE_SIZE,use_has_next='true',start_modified=s_dt_f,end_modified=s_dt_t)

            order_list = response_list['trades_sold_increment_get_response']
            if order_list.has_key('trades'):
                for trade in trades['trades']['trade']:

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
    try:
        user = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist,exc:
        logger.error('updateOrdersAmountTask error:%s'%exc, exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

    finish_trades = Trade.objects.filter(seller_id=user_id,consign_time__gte=update_from,consign_time__lte=update_to,
                                         is_update_amount=False,status=ORDER_FINISH_STATUS)

    error_times = 0

    for trade in finish_trades:
        try:
            response_list = apis.taobao_trade_amount_get(tid=trade.id,session=user.top_session)

            tamt = response_list['trade_amount_get_response']['trade_amount']
            trade.cod_fee = tamt['cod_fee']
            trade.total_fee = tamt['total_fee']
            trade.post_fee = tamt['post_fee']
            trade.commission_fee = tamt['commission_fee']
            trade.buyer_obtain_point_fee  = tamt['buyer_obtain_point_fee']
            trade.pay_time = parse_datetime(tamt['pay_time'])
            trade.is_update_amount = True
            trade.save()

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





@task(max_retry=3)
def saveUserOrdersLogisticsTask(user_id,days=0,update_from=None,update_to=None):
    try:
        user = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist,exc:
        logger.error('saveUserOrdersLogisticsTask error:%s'%exc, exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

    if not(update_from and update_to):
        dt = datetime.datetime.now()
        update_from = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0)-datetime.timedelta(days,0,0))
        update_to   = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0))


    has_next = True
    cur_page = 1
    error_times = 0

    while has_next:
        try:
            response_list = apis.taobao_logistics_orders_get(session=user.top_session,page_no=cur_page
                 ,page_size=settings.TAOBAO_PAGE_SIZE,start_created=update_from,end_created=update_to)

            logistics_list = response_list['logistics_orders_get_response']
            if logistics_list.has_key('shippings'):
                for t in logistics_list['shippings']['shipping']:

                    logistics,state = Logistics.objects.get_or_create(pk=t['tid'])
                    logistics.save_logistics_through_dict(user_id,t)

            total_nums = logistics_list['total_results']
            cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
            has_next = cur_nums<total_nums
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
            logger.error('update trade logistics fail',exc_info=True)
            raise e




@task()
def updateAllUserOrdersLogisticsTask(days=0,update_from=None,update_to=None):

    hander_update  = update_from and update_to
    if hander_update:
        update_from = format_datetime(update_from)
        update_to   = format_datetime(update_to)

    users = User.objects.all()

    for user in users:
        if hander_update:
            saveUserOrdersLogisticsTask(user.visitor_id,update_from=update_from,update_to=update_to)
        else:
            subtask(saveUserOrdersLogisticsTask).delay(user.visitor_id,days=days)




@task(max_retry=3)
def saveUserPurchaseOrderTask(user_id,update_from=None,update_to=None):
    try:
        user = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist:
        logger.error('saveUserPurchaseOrderTask error:%s'%exc, exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

    update_from = format_datetime(update_from)
    update_to   = format_datetime(update_to)

    has_next = True
    cur_page = 1
    error_times = 0

    while has_next:
        try:
            response_list = apis.taobao_fenxiao_orders_get(session=user.top_session,page_no=cur_page,
                time_type='trade_time_type',page_size=settings.TAOBAO_PAGE_SIZE/2,start_created=update_from,end_created=update_to)

            orders_list = response_list['fenxiao_orders_get_response']
            if orders_list['total_results']>0:
                for o in orders_list['purchase_orders']['purchase_order']:

                    order,state = PurchaseOrder.objects.get_or_create(pk=o['fenxiao_id'])
                    order.save_order_through_dict(user_id,o)

            total_nums = orders_list['total_results']
            cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
            has_next = cur_nums<total_nums
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
        except UserFenxiaoUnuseException:
            logger.error('the seller is not the user of fenxiao plateform',exc_info=True)
            break
        except AppCallLimitedException,e:
            logger.error('update trade purchase order fail',exc_info=True)
            raise e





@task()
def updateAllUserPurchaseOrderTask(update_from=None,update_to=None):

    hander_update  = update_from and update_to
    if not hander_update:
        dt  = datetime.datetime.now()
        update_from = datetime.datetime(dt.year,dt.month,dt.day,0,0,0)-datetime.timedelta(7,0,0)
        update_to   = datetime.datetime(dt.year,dt.month,dt.day,23,59,59)-datetime.timedelta(1,0,0)

    users = User.objects.all()
    interval_date = update_to - update_from

    for user in users:
        if hander_update:
            for i in range(0,interval_date.days/7+1):
                dt_f = update_from + datetime.timedelta(i*7,0,0)
                dt_t = update_from + datetime.timedelta((i+1)*7,0,0)
                saveUserPurchaseOrderTask(user.visitor_id,update_from=dt_f,update_to=dt_t)
        else:
            subtask(saveUserPurchaseOrderTask).delay(user.visitor_id,update_from=update_from,update_to=update_to)




@task(max_retry=3)
def saveUserRefundOrderTask(user_id,update_from=None,update_to=None):
    try:
        user = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist:
        logger.error('saveUserRefundOrderTask error:%s'%exc, exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

    update_from = format_datetime(update_from)
    update_to   = format_datetime(update_to)

    has_next = True
    cur_page = 1
    error_times = 0

    while has_next:
        try:
            response_list = apis.taobao_refunds_receive_get(session=user.top_session,page_no=cur_page,
                 page_size=settings.TAOBAO_PAGE_SIZE,start_modified=update_from,end_modified=update_to)

            refund_list = response_list['refunds_receive_get_response']
            if refund_list['total_results']>0:
                for r in refund_list['refunds']['refund']:

                    refund,state = Refund.objects.get_or_create(pk=r['refund_id'])
                    refund.save_refund_through_dict(user_id,r)

            total_nums = refund_list['total_results']
            cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
            has_next = cur_nums<total_nums
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
            logger.error('update refund orders fail',exc_info=True)
            raise e




@task()
def updateAllUserRefundOrderTask(days=0,update_from=None,update_to=None):

    hander_update  = update_from and update_to
    if not hander_update:
        dt  = datetime.datetime.now()
        update_from = datetime.datetime(dt.year,dt.month,dt.day,0,0,0)-datetime.timedelta(days,0,0)
        update_to   = datetime.datetime(dt.year,dt.month,dt.day,23,59,59)-datetime.timedelta(1,0,0)

    users = User.objects.all()
    for user in users:
        if hander_update:
            saveUserRefundOrderTask(user.visitor_id,update_from=update_from,update_to=update_to)
        else:
            subtask(saveUserRefundOrderTask).delay(user.visitor_id,update_from=update_from,update_to=update_to)




@task()
def updateMonthTradeXlsFileTask(year=None,month=None):

    dt = datetime.datetime.now()
    update_year_month = year and month
    if not update_year_month:
        last_month_date = dt - datetime.timedelta(dt.day,0,0)
    else:
        year,month = int(year),int(month)
        last_month_date = datetime.datetime(year,month,1,0,0,0)

    year_month = format_year_month(last_month_date)
    year       = last_month_date.year
    month      = last_month_date.month

    month_range = calendar.monthrange(year,month)
    last_month_first_days = datetime.datetime(year,month,1,0,0,0)
    last_month_last_days = datetime.datetime(year,month,month_range[1],23,59,59)

    time_delta = dt - last_month_last_days
    file_name  = settings.DOWNLOAD_ROOT+'/'+MONTH_TRADE_FILE_TEMPLATE%year_month

    if os.path.isfile(file_name) or not update_year_month or time_delta.days<settings.GEN_AMOUNT_FILE_MIN_DAYS:
        return {'error':'%s is already exist or must be ten days from last month at lest!'%file_name}

    start_date   = last_month_first_days - datetime.timedelta(7,0,0)

    users = User.objects.all()
    for user in users:
        report_status,state = MonthTradeReportStatus.objects.get_or_create\
                (seller_id=user.visitor_id,year=year,month=month)
        try:
            if not report_status.update_order:
                saveUserDuringOrders(user.visitor_id,update_from=start_date,update_to=dt)
                report_status.update_order = True

            if not report_status.update_purchase:
                interval_date = dt - start_date
                for i in range(0,interval_date.days/7+1):
                    dt_f = start_date + datetime.timedelta(i*7,0,0)
                    dt_t = start_date + datetime.timedelta((i+1)*7,0,0)
                    saveUserPurchaseOrderTask(user.visitor_id,update_from=dt_f,update_to=dt_t)
                report_status.update_purchase = True

            if not report_status.update_amount:
                updateOrdersAmountTask(user.visitor_id,update_from=last_month_first_days,update_to=dt)
                report_status.update_amount = True

            if not report_status.update_logistics:
                saveUserOrdersLogisticsTask(user.visitor_id,update_from=last_month_first_days,update_to=last_month_last_days)
                report_status.update_logistics = True

            if not report_status.update_refund:
                saveUserRefundOrderTask(user.visitor_id,update_from=start_date,update_to=last_month_last_days)
                report_status.update_refund = True

        except Exception,exc:
            report_status.save()
            logger.error('updateMonthTradeXlsFileTask excute error.',exc_info=True)
            return {'error':'%s'%exc}

        report_status.save()

    trade_file_builder = TradesToXLSFile()
    trade_file_builder.gen_report_file(last_month_first_days,last_month_last_days,file_name)

    return {'update_from':format_datetime(last_month_first_days),'update_to':format_datetime(last_month_last_days)}





