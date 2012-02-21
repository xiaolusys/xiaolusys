import datetime
import time
import json
import urllib
import urllib2
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from shopback.task.models import ItemListTask,UNEXECUTE,EXECERROR,SUCCESS
from shopback.users.models import User
from auth.utils import getSignatureTaoBao,refresh_session ,format_time
from auth import apis
import logging

from autolist.models import ProductItem, Logs

logger = logging.getLogger('updatelisting')

START_TIME = '00:00'
END_TIME = '23:59'

def write_to_log_db(task, response):
    log = Logs()

    item = ProductItem.objects.get(num_iid=task.num_iid)
    log.num_iid = item.num_iid
    log.num = task.num
    log.cat_id = item.category_id
    log.cat_name = item.category_name
    log.ref_code = item.ref_code
    log.title = item.title
    log.pic_url = item.pic_url
    log.list_weekday = task.list_weekday
    log.list_time = task.list_time
    log.task_type = task.task_type

    try:
        if task.task_type == "listing":
            log.status = response["item_update_listing_response"]["item"]["modified"]
        elif task.task_type == "delisting":
            log.status = response["item_update_delisting_response"]["item"]["modified"]
        elif task.task_type == "recommend":
            log.status = response["item_recommend_add_response"]["item"]["num_iid"]
        else:
            log.status = 'failed'
    except Exception:
        log.status = 'failed'
    
    log.save()


@task(max_retries=3)
def updateItemListTask(num_iid):

    try:
        task = ItemListTask.objects.get(num_iid=num_iid)
    except ItemListTask.DoesNotExist:
        logger.error('ItemListTask(num_iid:%s) Does Not Exist' %(num_iid))
        return

    success = True
    response = {'error_response':'the item num can not be updated!'}
    try:
        user = User.objects.get(visitor_id=task.user_id)

        refresh_session(user,settings.APPKEY,settings.APPSECRET,settings.REFRESH_URL)

        if task.task_type == 'listing':
            item = apis.taobao_item_get(num_iid=int(task.num_iid),session=user.top_session)

            if item.has_key('item_get_response') and item['item_get_response'].has_key('item') :
                task.num = int(item['item_get_response']['item']['num'])
                if item['item_get_response']['item']['approve_status'] == 'onsale':
                    response = apis.taobao_item_update_delisting(num_iid=task.num_iid,session=user.top_session)
                    task.task_type = "delisting"
                    write_to_log_db(task, response)

                    task.task_type = "listing"
                    response = apis.taobao_item_update_listing(num_iid=task.num_iid,num=task.num,session=user.top_session)
                    write_to_log_db(task, response)

                    if item['item_get_response']['item']['has_showcase'] == True:
                        task.task_type = "recommend"
                        response = apis.taobao_item_recommend_add(num_iid=task.num_iid,session=user.top_session)
                        write_to_log_db(task, response)
            else :
                success = False
                logger.warn('Get item unsuccess: %s'%item)

        elif task.task_type == 'delisting':
            item = apis.taobao_item_get(num_iid=task.num_iid,session=user.top_session)

            if item.has_key('item_get_response') and item['item_get_response'].has_key('item') :

                if item['item_get_response']['item']['approve_status'] == 'onsale':

                    response = apis.taobao_item_update_delisting\
                            (num_iid=task.num_iid,session=user.top_session)

                    task.num = item['num']
                else:
                    success = False
                    logger.warn('The item(%s) has been delisting: %s'%item)

            else :
                success = False
                logger.warn('Get item unsuccess: %s'%item)

        if response.has_key('error_response'):
            logger.error('Executing updateItemListTask(num_iid:%s) errorresponse:%s' %(task.num_iid,response))
            success = False

    except Exception,exc:
        success = False
        logger.error('Executing ItemListTask(id:%s) error:%s' %(num_iid,exc), exc_info=True)

    if success:
        task.status = SUCCESS
    else:
        task.status = EXECERROR

    task.save()


@task()
def updateAllItemListTask():
    currentdate = datetime.datetime.now()
    currenttime = time.mktime(currentdate.timetuple())
    weekday = currentdate.isoweekday()

    date_ago = datetime.datetime.fromtimestamp\
            (currenttime - settings.EXECUTE_RANGE_TIME)
    

    if date_ago.isoweekday() <weekday:
        time_ago = START_TIME
    else:
        time_ago = format_time(date_ago)

    date_future = datetime.datetime.fromtimestamp\
            (currenttime + settings.EXECUTE_RANGE_TIME)
    if date_future.isoweekday() >weekday:
        time_future = END_TIME
    else:
        time_future = format_time(date_future)

    tasks = ItemListTask.objects.filter\
            (list_weekday=weekday,list_time__gt=time_ago,list_time__lt=time_future,status=UNEXECUTE)

    for task in tasks:
        subtask(updateItemListTask).delay(task.num_iid)
