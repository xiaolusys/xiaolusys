import time
import datetime
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback.orders.models import Order,Trade,ORDER_FINISH_STATUS
from shopback.users.models import User
from auth.utils import format_time,format_datetime,parse_datetime,refresh_session
from auth import apis
import logging

logger = logging.getLogger('hourly.saveorder')
BLANK_CHAR = ''

@task(max_retry=3)
def saveUserDuringOrders(user_id,days=0):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist,exc:
        logger.error('SaveUserDuringOrders error:%s'%exc, exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

    dt = datetime.datetime.now()
    if days >0 :
        s_dt_f = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0)-datetime.timedelta(days,0,0))
        s_dt_t = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0))
    else:
        s_dt_f = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0))
        s_dt_t = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,dt.hour,59,59)-datetime.timedelta(0,1,0))

    has_next = True
    cur_page = 1
    trade = Trade()
    order = Order()

    while has_next:
        try:
            trades = apis.taobao_trades_sold_get(session=user.top_session,page_no=cur_page
                 ,page_size=settings.TAOBAO_PAGE_SIZE,use_has_next='true',start_created=s_dt_f,end_created=s_dt_t)

            if trades['trades_sold_increment_get_response'].has_key('trades'):
                for t in trades['trades_sold_get_response']['trades']['trade']:

                    trade.save_trade_through_dict(user_id,t)

                    order.seller_nick = t['seller_nick']
                    order.buyer_nick  = t['buyer_nick']
                    order.trade       = trade

                    for o in t['orders']['order']:
                        for k,v in o.iteritems():
                            hasattr(order,k) and setattr(order,k,v)
                        order.save()

            has_next = trades['trades_sold_get_response']['has_next']
            cur_page += 1
            time.sleep(0.5)
        except Exception,exc:
            time.sleep(60)




@task()
def updateAllUserDuringOrders(days):

    users = User.objects.all()

    for user in users:

        subtask(saveUserDuringOrders).delay(user.visitor_id,days=days)




@task(max_retry=3)
def saveUserDailyIncrementOrders(user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist,exc:
        logger.error('saveUserDailyIncrementOrders error:%s'%exc, exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

    dt = datetime.datetime.now()
    s_dt_f = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,0,0,0)-datetime.timedelta(1,0,0))
    s_dt_t = format_datetime(datetime.datetime(dt.year,dt.month,dt.day,23,59,59)-datetime.timedelta(1,0,0))

    has_next = True
    cur_page = 1
    trade = Trade()
    order = Order()

    while has_next:
        try:
            trades = apis.taobao_trades_sold_increment_get(session=user.top_session,page_size=settings.TAOBAO_PAGE_SIZE,
                 use_has_next='true',start_modified=s_dt_f,end_modified=s_dt_t)

            if trades['trades_sold_increment_get_response'].has_key('trades'):
                for t in trades['trades_sold_increment_get_response']['trades']['trade']:

                    trade.save_trade_through_dict(user_id,t)

                    order.seller_nick = t['seller_nick']
                    order.buyer_nick  = t['buyer_nick']
                    order.trade       = trade

                    for o in t['orders']['order']:
                        for k,v in o.iteritems():
                            hasattr(order,k) and setattr(order,k,v)
                        order.save()

            has_next = trades['trades_sold_increment_get_response']['has_next']
            cur_page += 1
            time.sleep(0.5)
        except Exception,exc:
            time.sleep(60)





@task()
def updateAllUserDailyIncrementOrders():

    users = User.objects.all()

    for user in users:

        subtask(saveUserDailyIncrementOrders).delay(user.visitor_id)




@task()
def updateOrdersAmountTask(user_id,f_dt,t_dt):
    try:
        user = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist,exc:
        logger.error('updateOrdersAmountTask error:%s'%exc, exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

    finish_trades = Trade.objects.filter(seller_id=user_id,created__gt=f_dt,created__lt=t_dt,
                                         commission_fee=BLANK_CHAR,status=ORDER_FINISH_STATUS)

    for trade in finish_trades:
        try:
            trade_amount = apis.taobao_trade_amount_get(tid=trade.id,session=user.top_session)
            if not trade_amount.has_key('trade_amount_get_response'):
                logger.warn('update trade amount fail:%s'%trade_amount)
                continue

            tamt = trade_amount['trade_amount_get_response']['trade_amount']
            trade.cod_fee = tamt['cod_fee']
            trade.total_fee = tamt['total_fee']
            trade.post_fee = tamt['post_fee']
            trade.commission_fee = tamt['commission_fee']
            trade.pay_time = parse_datetime(tamt['pay_time'])
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
                except Order.DoesNotExsit:
                    logger.error('the order(id:%s) does not exist'%o['oid'])

        except Exception,exc:
            logger.error('%s'%exc)


@task()
def updateAllUserOrdersAmountTask():

    dt = datetime.datetime.now()
    f_dt = datetime.datetime(dt.year,dt.month,dt.day,0,0,0)\
        - datetime.timedelta(7,0,0)
    t_dt = datetime.datetime(dt.year,dt.month,dt.day,23,59,59)\
        - datetime.timedelta(1,0,0)

    users = User.objects.all()
    for user in users:

        subtask(updateOrdersAmountTask).delay(user.visitor_id,f_dt,t_dt)




