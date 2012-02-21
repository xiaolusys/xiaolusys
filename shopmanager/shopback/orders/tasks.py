import datetime
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback.orders.models import Order
from shopback.users.models import User
from auth.utils import format_time,format_datetime
from auth import apis
import logging

logger = logging.getLogger('hourly.saveorder')


@task(max_retry=3)
def saveUserHourlyOrders(user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        pass
    dt = datetime.datetime.now()
    #dt = datetime.datetime(2012,2,20,14,20)

    year = dt.year
    month = dt.month
    day = dt.day
    hour = dt.hour-1

    s_dt_f = format_datetime(datetime.datetime(year,month,day,hour,0,0))
    s_dt_t = format_datetime(datetime.datetime(year,month,day,hour,59,59))

    has_next = True
    cur_page = 1
    order = Order()

    order.month = month
    order.day = day
    order.hour = hour
    try:
        while has_next:
            trades = apis.taobao_trades_sold_get(session=user.top_session,page_no=cur_page,
                 page_size=settings.GET_TAOBAO_DATA_PAGE_SIZE,use_has_next='true',start_created=s_dt_f,end_created=s_dt_t)

            if trades.has_key('error_response'):
                logger.error('Get users trades errorresponse:%s' %(trades))
                break

            if trades['trades_sold_get_response']['total_results']>0:
                for t in trades['trades_sold_get_response']['trades']['trade']:

                    order.created = t['created']
                    order.seller_nick = t['seller_nick']
                    order.buyer_nick = t['buyer_nick']
                    order.modified = t['modified']

                    for o in t['orders']['order']:

                        for k,v in o.iteritems():
                            hasattr(order,k) and setattr(order,k,v)
                        order.save()

            has_next = trades['trades_sold_get_response']['has_next']
            cur_page += 1

    except Exception,exc:

        logger.error('Executing saveUserHourlyOrders error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            saveUserHourlyOrders.retry(exc=exc,countdown=2)





@task()
def updateAllUserOrders():

    users = User.objects.all()

    for user in users:

        subtask(saveUserHourlyOrders).delay(user.pk)
        #saveUserHourlyOrders(user.pk)




