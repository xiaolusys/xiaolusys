import datetime
import time
import json
import urllib
import urllib2
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback.base.aggregates import ConcatenateDistinct
from auth.utils import format_datetime ,parse_datetime ,refresh_session
from shopback.items.models import Item
from shopback.orders.models import Order
from shopback.users.models import User
from shopback.task.models import ItemNumTask,UNEXECUTE,EXECERROR,SUCCESS
from auth import apis
import logging

logger = logging.getLogger('updateitemnum')

ORDER_SUCCESS_STATUS = ['WAIT_SELLER_SEND_GOODS','WAIT_BUYER_CONFIRM_GOODS','TRADE_BUYER_SIGNED','TRADE_FINISHED']

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

@task(max_retry=3)
def updateUnpayOrderTask(tid,nick):

    try:
        user = User.objects.get(nick=nick)

        refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)
    except Exception,exc:
        logger.error('Excute updateUnpoyOrderTask error:%s'%exc,exc_info=True)
        return

    try:
        trades = apis.taobao_trade_fullinfo_get(tid,session=user.top_session)

        if trades.has_key('error_response'):
            logger.error('Excute updateUnpoyOrderTask %s'%trades)
            return

        t = trades['trade_fullinfo_get_response']['trade']

        for order in  t['orders']['order']:
            try:
                order_obj = Order.objects.get(oid=order['oid'])
                order_obj.modified = t['modified']

                for k,v in order.iteritems():
                    hasattr(order_obj,k) and setattr(order_obj,k,v)
                order_obj.save()

            except Exception,exc:
                logger.error('Excute updateUnpoyOrderTask error:%s'%exc,exc_info=True)

    except Exception,exc:
        logger.error('Excute updateUnpoyOrderTask error:%s'%exc,exc_info=True)
        if not settings.DEBUG:
            pullPerUserTradesTask.retry(exc=exc,countdown=2)


@task()
def updateAllUnpayOrderTask():

    unpay_orders = Order.objects.filter(status='WAIT_BUYER_PAY')\
        .values('tid','seller_nick').distinct('tid')

    for order in unpay_orders:
        subtask(updateUnpayOrderTask).delay(order['tid'],order['seller_nick'])



@task(max_retries=3)
def pullPerUserTradesTask(user_id,start_created,end_created):

    try:
        user = User.objects.get(pk=user_id)

        refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)
    except User.DoesNotExist:
        logger.error('Executing pullPerUserTrades error:%s' %(exc), exc_info=True)
        return

    has_next = True
    cur_page = 1

    try:
        while has_next:

            trades = apis.taobao_trades_sold_increment_get(session=user.top_session,page_no=1,page_size=200,
                     start_modified=start_created,end_modified=end_created,use_has_next='true')

            if trades.has_key('error_response'):
                logger.error('Get users trades errorresponse:%s' %(trades))
                break

            if trades['trades_sold_get_increment_response']['total_results']>0:

                order_obj = Order()
                for t in trades['trades_sold_get_increment_response']['trades']['trade']:

                    dt = parse_datetime(t['created'])
                    order_obj.month = dt.month
                    order_obj.day = dt.day
                    order_obj.hour = dt.strftime("%H")
                    order_obj.week = time.gmtime(time.mktime(dt.timetuple()))[7]/7+1
                    order_obj.created = t['created']
                    order_obj.seller_nick = t['seller_nick']
                    order_obj.buyer_nick = t['buyer_nick']
                    order_obj.modified = t['modified']
                    order_obj.tid = t['tid']

                    for order in t['orders']['order']:

                        for k,v in order.iteritems():
                            hasattr(order_obj,k) and setattr(order_obj,k,v)

                        order_obj.save()

                        if order['status'] in ORDER_SUCCESS_STATUS and t['created']>=start_created:

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

            has_next = trades['trades_sold_increment_get_response']['has_next']
            cur_page += 1

    except Exception,exc:

        logger.error('Executing pullPerUserTradesTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            pullPerUserTradesTask.retry(exc=exc,countdown=2)




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

        time.sleep(settings.UPDATE_UNPAY_ORDER_INTERVAL)
        print '----------------excute updateAllUnpayOrderTask start---------------'
        subtask(updateAllUnpayOrderTask).delay()

    except Exception,exc:

        logger.error('Executing UpdateAllItemNumTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            updateAllItemNumTask.retry(exc=exc,countdown=2)


@task(max_retries=3)
def saveItemInfoTask(num_iid):
    try:
        item = Item.objects.get(num_iid=num_iid)

        user = User.objects.get(visitor_id=item.user_id)

        refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)
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




  