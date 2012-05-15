import time
import datetime
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback.orders.models import Order,Trade
from shopback.users.models import User
from auth.utils import format_time,format_datetime,parse_datetime,refresh_session
from auth import apis
import logging

logger = logging.getLogger('hourly.saveorder')


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

            for t in trades['trades_sold_get_response']['trades']['trade']:

                trade.save_trade_through_dict(t)

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

        subtask(saveUserDuringOrders).delay(user.pk,days=days)




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

            for t in trades['trades_sold_increment_get_response']['trades']['trade']:
                trade.save_trade_through_dict(t)

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

        subtask(saveUserDailyIncrementOrders).delay(user.pk)









