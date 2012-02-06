import datetime
import time
import json
import urllib
import urllib2
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from auth.utils import getSignatureTaoBao,refresh_session,format_datetime
from shopback.items.models import Item
from shopback.orders.models import Order
from shopback.users.models import User
from auth import apis
import logging

logger = logging.getLogger('updateitemnum')

@task(max_retries=3)
def updateItemNumTask(num_iid,num,top_session):

    try:
        item = Item.objects.get(num_iid=num_iid)

        item.num -= num
        if item.num <0:
            item.num=0

        apis.taobao_item_update(num_iid=num_iid,num=item.num,session=top_session)

        item.save()

    except Exception,exc:
        print 'debug update exc:',exc
        logger.error('Executing UpdateItemNumTask(outer_iid:%s,num_iid:%s) error:%s' %(outer_iid,num_iid,exc), exc_info=True)
        if not settings.DEBUG:
            create_comment.retry(exc=exc,countdown=2)


@task(max_retries=3)
def saveDailyOrdersTask(orders_list):

    try:
        for order in orders_list:
            try:
                o = Order.objects.get(oid=order['oid'])
            except Order.DoesNotExist:
                o = Order()
                for k,v in order.iteritems():
                    hasattr(o,k) and setattr(o,k,v)
                o.save()

    except Exception,exc:
        print 'debug save order:',exc
        logger.error('Executing saveDailyOrdersTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            create_comment.retry(exc=exc,countdown=2)


@task(max_retries=3)
def pullPerUserTradesTask(user_id,start_created,end_created):

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error('Executing pullPerUserTrades error:%s' %(exc), exc_info=True)

    try:
        trades = apis.taobao_trades_sold_get(session=user.top_session,page_no=1,page_size=200,
                 start_created=start_created,end_created=end_created)
#        trades = apis.taobao_trades_sold_get(session=user.top_session,page_no=1,page_size=200,
#               start_created='2012-02-03 00:00:00',end_created='2012-02-03 23:59:59')
    except Exception,exc:
        print 'debug save order:',exc
        logger.error('Executing pullPerUserTradesTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            create_comment.retry(exc=exc,countdown=2)

    orders_list = []
    order_items = {}

    for t in trades['trades_sold_get_response']['trades']['trade']:
        orders_list.extend(t['orders']['order'])

    if orders_list:
        subtask(saveDailyOrdersTask).delay(orders_list)
    print 'debug trades:',len(orders_list)
    for order in orders_list:
        if order_items.has_key(order['outer_iid']):
            order_items[order['outer_iid']] += order['num']
        else:
            order_items[order['outer_iid']] = order['num']

    for outer_iid,num in order_items.iteritems():
        try:
            items = Item.objects.filter(outer_iid=outer_iid,user_id=user.visitor_id)

            for item in items:
                print 'debug item:',item.__dict__
                subtask(updateItemNumTask).delay(item.num_iid,num,user.top_session)
                break;
        except Exception,exc :

            logger.error('Executing UpdateItemNum(outer_iid:%s) error:%s' %(outer_iid,exc), exc_info=True)


@task(max_retries=3)
def updateAllItemNumTask():

    try:
        cur_dt = datetime.datetime.now()
        dt = datetime.datetime(cur_dt.year,cur_dt.month,cur_dt.day)

        ttuple = time.mktime(dt.timetuple())

        lastday_start_datetime = datetime.datetime.fromtimestamp(ttuple-24*60*60)
        lastday_end_datetime = datetime.datetime.fromtimestamp(ttuple-1)

        updatenum_users = User.objects.exclude(update_items_datetime=None)

        for user in updatenum_users:

            update_datetime = user.update_items_datetime

            if update_datetime:

#                timedelta = lastday_end_datetime - update_datetime
#
#                if timedelta.days < 0:
#                    continue
#
#                if timedelta.days < 1:
#                    start_datetime = format_datetime(update_datetime)
#
#                if timedelta.days >= 1:
#                    start_datetime = format_datetime(lastday_start_datetime)

                start_datetime = format_datetime(update_datetime)
                end_datetime = format_datetime(lastday_end_datetime)

                #trades = apis.taobao_trades_sold_get(session=user.top_session,page_no=1,page_size=200,
                #        start_created=start_datetime,end_created=end_datetime)

                #subtask(pullPerUserTradesTask).delay(user.id,start_datetime,end_datetime)

                trades = apis.taobao_trades_sold_get(session=user.top_session,page_no=1,page_size=200,
                        start_created='2012-02-03 00:00:00',end_created='2012-02-03 23:59:59')

                orders_list = []
                order_items = {}

                for t in trades['trades_sold_get_response']['trades']['trade']:
                    orders_list.extend(t['orders']['order'])

                if orders_list:
                    subtask(saveDailyOrdersTask).delay(orders_list)
                print 'debug trades:',len(orders_list)
                for order in orders_list:
                    if order_items.has_key(order['outer_iid']):
                        order_items[order['outer_iid']] += order['num']
                    else:
                        order_items[order['outer_iid']] = order['num']

                for outer_iid,num in order_items.iteritems():
                    try:
                        items = Item.objects.filter(outer_iid=outer_iid,user_id=user.visitor_id)

                        for item in items:
                            print 'debug item:',item.__dict__
                            subtask(updateItemNumTask).delay(item.num_iid,num,user.top_session)
                            break;
                    except Exception,exc :

                        logger.error('Executing UpdateItemNum(outer_iid:%s) error:%s' %(outer_iid,exc), exc_info=True)

    except Exception,exc:
        logger.error('Executing UpdateAllItemNumTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            create_comment.retry(exc=exc,countdown=2)







  