import datetime
import time
import json
import urllib
import urllib2
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from shopback.task.models import ItemListTask
from shopback.users.models import User
from auth.utils import getSignatureTaoBao,refresh_session
from auth import apis
import logging

logger = logging.getLogger('updatelisting')

@task(max_retries=3)
def updateItemListTask(task_id):

    try:

        task = ItemListTask.objects.get(pk=task_id,status=True,is_success=False)

        user = User.objects.get(visitor_id=task.visitor_id)

        if task.task_type == 1:

            update_ret = apis.taobao_item_update_listing(num_iid=task.num_iid,num=task.num,session=user.top_session)

            if update_ret.get('item_update_listing_response',None) and\
               update_ret['item_update_listing_response'].get('item',None):
                task.is_success = True
            else :
                logger.warn('Update itemlist unsuccess: %s'%update_ret)
        elif task.task_type == 2:
            item = apis.taobao_item_get(num_iid=task.num_iid,session=user.top_session)

            if item.has_key('item_get_response') and item['item_get_response'].has_key('item') :

                if item['item_get_response']['item']['approve_status'] == 'onsale':

                    del_ret = apis.taobao_item_update_delisting(num_iid=task.num_iid,session=user.top_session)
                    if del_ret.get('item_update_delisting_response',None) and \
                        del_ret['item_update_delisting_response'].get('item',None):
                        task.is_success = True
                    else :
                        logger.warn('Delete itemlist unsuccess: %s'%del_ret)
            else :
                logger.warn('Get item unsuccess: %s'%item)

        task.save()

    except Exception,exc:
        logger.error('Executing ItemListTask(id:%s) error:%s' %(task_id,exc), exc_info=True)
        from django.conf import settings
        if not settings.DEBUG:
            create_comment.retry(exc=exc,countdown=1)



@task()
def updateAllItemListTask():

    currenttime = time.time()
    timeago = datetime.datetime.fromtimestamp(currenttime - settings.EXECUTE_RANGE_TIME)
    timefuture = datetime.datetime.fromtimestamp(currenttime + settings.EXECUTE_RANGE_TIME)

    tasks = ItemListTask.objects.filter(update_time__gt=timeago,update_time__lt=timefuture,status=True,is_success=False)

    for task in tasks:

        subtask(updateItemListTask).delay(task.id)




