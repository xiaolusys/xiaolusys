#-*- coding:utf-8 -*-
import datetime
import time
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from shopback.users.models import User
from shopback.items.models import Item
from shopapp.autolist.models import Logs,ItemListTask,SUCCESS,EXECERROR,UNEXECUTE
from auth.utils import getSignatureTaoBao,format_time
from auth import apis
import logging



logger = logging.getLogger('autolist.handler')

START_TIME = '00:00'
END_TIME = '23:59'
#商品上架时间幅度，当前时间加减后的时间间隔
EXECUTE_RANGE_TIME = 3*60
#

def write_to_log_db(task, response):
    log = Logs()

    item = Item.objects.get(num_iid=task.num_iid)
    log.num_iid = item.num_iid
    log.num = task.num
    log.cat_id = item.category.cid if item.category else 0
    log.cat_name = item.category.name if item.category else ''
    log.outer_id = item.outer_id
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


@task(max_retry=3)
def updateItemListTask(num_iid):

    try:
        task = ItemListTask.objects.get(num_iid=num_iid)
    except ItemListTask.DoesNotExist:
        logger.error('ItemListTask(num_iid:%s) Does Not Exist' %(num_iid))
        return

    success = True
    response = {'error_response':u'商品上下架失败！'}
    try:
        if task.task_type == 'listing':
            item = apis.taobao_item_get(num_iid=int(task.num_iid),tb_user_id=task.user_id)

            if item.has_key('item_get_response') and item['item_get_response'].has_key('item') :
                task.num = int(item['item_get_response']['item']['num'])
                if item['item_get_response']['item']['approve_status'] == 'onsale':
                    response = apis.taobao_item_update_delisting(num_iid=task.num_iid,tb_user_id=task.user_id)
                    task.task_type = "delisting"
                    write_to_log_db(task, response)
                
                task.task_type = "listing"
                response = apis.taobao_item_update_listing(num_iid=task.num_iid,num=task.num,tb_user_id=task.user_id)
                write_to_log_db(task, response)
                
                Item.objects.filter(num_iid=num_iid).update(list_time=response['item_update_listing_response']['item']['modified'])
                
                if item['item_get_response']['item']['has_showcase'] == True:
                    task.task_type = "recommend"
                    response = apis.taobao_item_recommend_add(num_iid=task.num_iid,tb_user_id=task.user_id)
                    write_to_log_db(task, response)
            else :
                success = False

        elif task.task_type == 'delisting':
            item = apis.taobao_item_get(num_iid=task.num_iid,tb_user_id=task.user_id)

            if item.has_key('item_get_response') and item['item_get_response'].has_key('item') :
                if item['item_get_response']['item']['approve_status'] == 'onsale':
                    response = apis.taobao_item_update_delisting(num_iid=task.num_iid,tb_user_id=task.user_id)
                    task.num = item['num']
                else:
                    success = False
            else :
                success = False

        if response.has_key('error_response'):
            logger.error(u'上下架任务未成功(商品ID:%s) 原因:%s'%(task.num_iid,response['error_response']))
            success = False

    except Exception,exc:
        success = False
        logger.error(u'上下架任务异常(商品ID:%s) 错误:%s' %(num_iid,exc), exc_info=True)

    if success:
        task.status = SUCCESS
    else:
        task.status = EXECERROR

    task.save()


@apis.single_instance_task(30*60,prefix='shopapp.autolist.tasks.')
def updateAllItemListTask():
    currentdate = datetime.datetime.now()
    currenttime = time.mktime(currentdate.timetuple())
    weekday = currentdate.isoweekday()

    date_ago = datetime.datetime.fromtimestamp\
            (currenttime - EXECUTE_RANGE_TIME)


    if date_ago.isoweekday() <weekday:
        time_ago = START_TIME
    else:
        time_ago = format_time(date_ago)

    date_future = datetime.datetime.fromtimestamp\
            (currenttime + EXECUTE_RANGE_TIME)
    if date_future.isoweekday() >weekday:
        time_future = END_TIME
    else:
        time_future = format_time(date_future)

    tasks = ItemListTask.objects.filter\
            (list_weekday=weekday,list_time__gte=time_ago,list_time__lte=time_future,status=UNEXECUTE)

    for task in tasks:
        updateItemListTask(task.num_iid)


