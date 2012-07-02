import json
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback.base.aggregates import ConcatenateDistinct
from auth.utils import format_datetime ,parse_datetime ,refresh_session
from shopback.items.models import Item
from shopback.orders.models import Order,Trade,ORDER_SUCCESS_STATUS,ORDER_UNPAY_STATUS
from shopback.users.models import User
from shopapp.syncnum.models import ItemNumTask
from shopback.base.models import UNEXECUTE,EXECERROR,SUCCESS
from auth.apis.exceptions import RemoteConnectionException,AppCallLimitedException,UserFenxiaoUnuseException,\
    APIConnectionTimeOutException,ServiceRejectionException,TaobaoRequestException
from auth import apis
import logging

logger = logging.getLogger('syncnum.handler')


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
        except exc.AppCallLimitedException,e:
            logger.error('update trade during order task fail',exc_info=True)
            raise e
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
def pullPerUserTradesTask(user_id,start_created,end_created):

    try:
        user = User.objects.get(pk=user_id)

    except User.DoesNotExist:
        logger.error('Executing pullPerUserTrades error:%s' %(exc), exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

    has_next = True
    cur_page = 1
    order_obj = Order()

    while has_next:
        try:
            response = apis.taobao_trades_sold_increment_get(session=user.top_session,page_no=cur_page,use_has_next='true',
                    page_size=settings.TAOBAO_PAGE_SIZE,start_modified=start_created,end_modified=end_created)

            trades = response['trades_sold_increment_get_response']
            if trades.has_key('trades') and trades.get('trades').has_key('trade'):

                for t in trades['trades']['trade']:

                    trade,state = Trade.objects.get_or_create(pk=t['tid'])
                    trade.save_trade_through_dict(user_id,t)

                    order_obj.seller_nick = t['seller_nick']
                    order_obj.buyer_nick  = t['buyer_nick']
                    order_obj.trade       = trade

                    for order in t['orders']['order']:
                        for k,v in order.iteritems():
                            hasattr(order_obj,k) and setattr(order_obj,k,v)

                        order_obj.save()

                        if order['status'] in ORDER_SUCCESS_STATUS \
                            and t['created']>=start_created \
                            and order.get('outer_iid',None):

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

            has_next = trades['has_next']
            cur_page += 1
            time.sleep(5)

        except exc.AppCallLimitedException,e:
            logger.error('update trade during order task fail',exc_info=True)
            raise e
        except Exception,exc:
            time.sleep(120)





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

    except Exception,exc:

        logger.error('Executing UpdateAllItemNumTask error:%s' %(exc), exc_info=True)
        if not settings.DEBUG:
            updateAllItemNumTask.retry(exc=exc,countdown=2)


