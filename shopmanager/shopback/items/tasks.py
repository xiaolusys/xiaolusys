import datetime
import time
import json
import urllib
import urllib2
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from auth.utils import format_datetime
from shopback.items.models import Item
from shopback.orders.models import Order
from shopback.users.models import User
from shopback.task.models import ItemNumTask,UNEXECUTE,EXECERROR,SUCCESS
from auth import apis
import logging

logger = logging.getLogger('updateitemnum')


@task(max_retries=3)
def updateItemNumTask(itemNumTask_id):
    try:
        itemNumTask = ItemNumTask.objects.get(id=itemNumTask_id)
    except ItemNumTask.DoesNotExist:
        logger.error('ItemNumTask(id:%s) is not valid!' %(itemNum_id))
        return

    success = True
    items = Item.objects.filter(outer_iid=itemNumTask.outer_iid)

    for item in items:
        try:
            user = User.objects.get(visitor_id=item.user_id)

            item.num -= itemNumTask.num

            skus = json.loads(item.skus)
            sku_outer_id = itemNumTask.sku_outer_id
            response = {'error_response':'the item num can not be updated!'}

            if skus:

                for sku in skus.get('sku',[]):
                    outer_id = sku.get('outer_id','')
                    if  sku_outer_id == outer_id:
                        sku['quantity'] -= itemNumTask.num

                        response = apis.taobao_item_quantity_update\
                                (num_iid=item.num_iid,quantity=sku['quantity'],sku_id=sku['sku_id'],session=user.top_session)
                        item.skus = json.dumps(skus)
                        break

            else:
                response = apis.taobao_item_update(num_iid=item.num_iid,num=item.num,session=user.top_session)

            if response.has_key('error_response'):
                logger.error('Executing UpdateItemNumTask(num_iid:%s) errorresponse:%s' %(item.num_iid,response))
                success = False
            else:
                item.save()

        except Exception,exc:
            success = False
            logger.error('Executing UpdateItemNumTask(num_iid:%s) error:%s' %(item.num_iid,exc), exc_info=True)
            if not settings.DEBUG:
                updateItemNumTask.retry(exc=exc,countdown=2)

    if success:
        itemNumTask.status = SUCCESS
    else:
        itemNumTask.status = EXECERROR

    itemNumTask.save()


@task()
def execAllItemNumTask():

    itemNumTasks = ItemNumTask.objects.filter(status=UNEXECUTE)

    for itemNumTask in itemNumTasks:
        subtask(updateItemNumTask).delay(itemNumTask.id)



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

        logger.error('Executing saveDailyOrdersTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            saveDailyOrdersTask.retry(exc=exc,countdown=2)


@task(max_retries=3)
def pullPerUserTradesTask(user_id,start_created,end_created):

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error('Executing pullPerUserTrades error:%s' %(exc), exc_info=True)
        return

    try:
        trades = apis.taobao_trades_sold_increment_get(session=user.top_session,page_no=1,page_size=200,
                 start_modified=start_created,end_modified=end_created,use_has_next='true')

        #trades = apis.taobao_trades_sold_get(session=user.top_session,page_no=1,page_size=200,
        #       start_created='2012-02-03 00:00:00',end_created='2012-02-03 23:59:59')
    except Exception,exc:

        logger.error('Executing pullPerUserTradesTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            pullPerUserTradesTask.retry(exc=exc,countdown=2)

    if trades.has_key('error_response'):
        logger.warn('Get users trades errorresponse:%s' %(trades))
        return

    orders_list = []

    if trades['trades_sold_get_response']['total_results']>0:
        for t in trades['trades_sold_get_response']['trades']['trade']:
            orders_list.extend(t['orders']['order'])

    if orders_list:
        subtask(saveDailyOrdersTask).delay(orders_list)


    for order in orders_list:

        if order['status'] != 'TRADE_CLOSED_BY_TAOBAO' and order['status'] != 'WAIT_BUYER_PAY':
            sku_outer_id = order.get('outer_sku_id','')
            try:
                itemNumTask = ItemNumTask.objects.get\
                        (outer_iid=order['outer_iid'],sku_outer_id=sku_outer_id,status=UNEXECUTE)
                itemNumTask.num += order['num']
            except ItemNumTask.DoesNotExist:
                itemNumTask = ItemNumTask()
                itemNumTask.outer_iid = order['outer_iid']
                itemNumTask.sku_outer_id = sku_outer_id
                itemNumTask.num = order['num']

            itemNumTask.save()



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

                timedelta = lastday_end_datetime - update_datetime

                if timedelta.days < 0:
                    continue

                if timedelta.days < 1:
                    start_datetime = format_datetime(update_datetime)

                if timedelta.days >= 1:
                    start_datetime = format_datetime(lastday_start_datetime)

                #start_datetime = format_datetime(lastday_start_datetime)

                end_datetime = format_datetime(lastday_end_datetime)

                subtask(pullPerUserTradesTask).delay(user.id,start_datetime,end_datetime)

        time.sleep(settings.UPDATE_ITEM_NUM_INTERVAL)
        print '----------------excute updateAllItemNumTask start---------------'
        subtask(execAllItemNumTask).delay()

    except Exception,exc:

        logger.error('Executing UpdateAllItemNumTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            updateAllItemNumTask.retry(exc=exc,countdown=2)


@task(max_retries=3)
def saveItemInfoTask(num_iid):
    try:
        item = Item.objects.get(num_iid=num_iid)

        user = User.objects.get(visitor_id=item.user_id)
    except User.DoesNotExist:
        logger.error('User(id:%s) not valide!' %(item.user_id))

    try:
        response = apis.taobao_item_get(num_iid=num_iid,session=user.top_session)
    except Exception,exc:
        logger.error('Executing saveItemInfoTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            saveItemInfoTask.retry(exc=exc,countdown=2)

    if response.has_key('error_response'):
        logger.error('Executing saveItemInfoTask(num_iid:%s) errorresponse:%s' %(num_iid,response))
    else:
        itemdict = response['item_get_response']['item']
        itemdict['skus'] = json.dumps(itemdict.get('skus',{}))

        for k,v in itemdict.iteritems():
            hasattr(item,k) and setattr(item,k,v)

        item.save()





@task()
def updateItemsInfoTask(user_id):

    items = Item.objects.filter(user_id=user_id)

    for item in items:

        subtask(saveItemInfoTask).delay(item.num_iid)




  