import datetime
import time
import json
import urllib
import urllib2
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from auth.utils import getSignatureTaoBao,refresh_session,format_datetime
from shopback.items.models import Item
from shopback.orders.models import Order
from auth import apis
import logging

logger = logging.getLogger('updateitemnum')

@task(max_retries=3)
def updateItemNumTask():

    try:
        item = Item.objects.get(outer_iid=outer_iid)
        session = SessionStore(session_key=session_key)

        refresh_success = refresh_session(session,settings)

        if refresh_success:
            session.save()

        item.num -= num
        if item.num <0:
            item.num=0

        apis.taobao_item_update(num_iid=num_iid,num=item.num,session=session['top_session'])

        item.save()

    except Exception,exc:
        logger.error('Executing UpdateItemNumTask(outer_iid:%s,num_iid:%s) error:%s' %(outer_iid,num_iid,exc), exc_info=True)
        if not settings.DEBUG:
            create_comment.retry(exc=exc,countdown=2)

@task(max_retries=3)
def saveDailyOrdersTask(orders_list):

    try:
        o = Order()
        for order in orders_list:
            o.id = None
            for k,v in order.iteritems():
                hasattr(o,k) and setattr(o,k,v)
            o.save()

    except Exception,exc:
        print exc
        logger.error('Executing saveDailyOrdersTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            create_comment.retry(exc=exc,countdown=2)



@task(max_retries=3)
def updateAllItemNumTask():

    try:
        cur_dt = datetime.datetime.now()
        dt = datetime.datetime(cur_dt.year,cur_dt.month,cur_dt.day)

        ttuple = time.mktime(dt.timetuple())

        lastday_start_datetime = datetime.datetime.fromtimestamp(ttuple-24*60*60)
        lastday_end_datetime = datetime.datetime.fromtimestamp(ttuple-1)

        sessions = Session.objects.all()

        for session in sessions:

            session = session.get_decoded()
            update_datetime = session.get('update_items_datetime',None)

            if update_datetime:

                timedelta = lastday_end_datetime - update_datetime

                if timedelta.days < 0:
                    continue

                if timedelta.days < 1:
                    start_datetime = format_datetime(update_datetime)

                if timedelta.days >= 1:
                    start_datetime = format_datetime(lastday_start_datetime)


                end_datetime = format_datetime(lastday_end_datetime)

                trades = apis.taobao_trades_sold_get(session=session['top_session'],page_no=1,page_size=200,
                        start_created=start_datetime,end_created=end_datetime)

                #trades = apis.taobao_trades_sold_get(session=session['top_session'],page_no=1,page_size=200,
                #start_created='2012-02-02 00:00:00',end_created='2012-02-02 23:59:59')

                orders_list = []
                order_items = {}

                for t in trades['trades_sold_get_response']['trades']['trade']:
                    orders_list.extend(t['orders']['order'])

                if orders_list:
                    print 'save orders'
                    subtask(saveDailyOrdersTask).delay(orders_list)

                for order in orders_list:
                    if order_items.has_key(order['outer_iid']):
                        order_items[order['outer_iid']] += order['num']
                    else:
                        order_items[order['outer_iid']] = order['num']

                for outer_iid,num in order_items.iteritems():
                    try:
                        item = Item.objects.get(outer_iid=outer_iid)
                        numiid_sessions = json.loads(item.numiid_session)

                        for numsess in numiid_sessions:
                            numiid_session = numsess.split(':')

                            #subtask(updateItemNumTask).delay(outer_iid,numiid_session[0],num,numiid_session[1])

                    except Exception,exc :

                        logger.error('Executing UpdateItemNum(outer_iid:%s) error:%s' %(outer_iid,exc), exc_info=True)

    except Exception,exc:
        logger.error('Executing UpdateAllItemNumTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            create_comment.retry(exc=exc,countdown=2)







  