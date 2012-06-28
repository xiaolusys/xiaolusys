import datetime
import time
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
from shopback.base.models   import UNEXECUTE,EXECERROR,SUCCESS
from auth.apis.exceptions import RemoteConnectionException,AppCallLimitedException,UserFenxiaoUnuseException,\
    APIConnectionTimeOutException,ServiceRejectionException,TaobaoRequestException
from auth import apis
import logging

logger = logging.getLogger('updateitem')



@task()
def updateUserItemsTask(user_id):
    try:
        user = User.objects.get(visitor_id=user_id)
    except User.DoesNotExist,exc:
        logger.error('User(pk:%d) does not exist.'%user_id, exc_info=True)
        return

    refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

    has_next = True
    cur_page = 1
    error_times = 0
    update_nums = 0

    while has_next:
        try:
            response_list = apis.taobao_items_onsale_get(session=user.top_session,page_no=cur_page
                ,page_size=settings.TAOBAO_PAGE_SIZE)

            item_list = response_list['items_onsale_get_response']
            if item_list.has_key('items'):
                for item in item_list['items']['item']:
                    Item.save_item_through_dict(user_id,item)

            total_nums = item_list['total_results']
            cur_nums = cur_page*settings.TAOBAO_PAGE_SIZE
            has_next = cur_nums<total_nums
            cur_page += 1
            error_times = 0
            update_nums += total_nums
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

    return update_nums




@task()
def updateAllUserItemsTask():
    users = User.objects.all()

    for user in users:
        subtask(updateUserItemsTask).delay(user.visitor_id)




@task(max_retries=3)
def saveUserItemsInfoTask(user_id):

    items = Item.objects.filter(user_id=user_id)
    for item in items:
        user = User.objects.get(visitor_id=user_id)

        try:
            response = apis.taobao_item_get(num_iid=item.num_iid,session=user.top_session)
            itemdict = response['item_get_response']['item']
            itemdict['skus'] = json.dumps(itemdict.get('skus',{}))

            for k,v in itemdict.iteritems():
                hasattr(item,k) and setattr(item,k,v)
            item.save()

        except AppCallLimitedException,e:
            logger.error('update trade during order task fail',exc_info=True)
            raise e
        except TaobaoRequestException,e:
            logger.error('update trade during order task fail',exc_info=True)
            if not settings.DEBUG:
                updateAllItemNumTask.retry(exc=exc,countdown=2)




@task()
def updateAllUserItemsInfoTask():

    users = User.objects.all()
    for user in users:

        subtask(saveUserItemsInfoTask).delay(user.visitor_id)




  