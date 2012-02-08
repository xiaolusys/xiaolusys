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
        task = ItemListTask.objects.get(pk=task_id)
    except ItemListTask.DoesNotExist:
        logger.error('ItemListTask(task_id:%s) Does Not Exist' %(task_id))
        return

    success = True
    response = {'error_response':'The task(task_id:%s) is not valid'%(task_id)}
    try:

        user = User.objects.get(visitor_id=task.user_id)

        if task.task_type == 'listing':
            response = apis.taobao_item_update_listing\
                    (num_iid=task.num_iid,num=task.num,session=user.top_session)

        elif task.task_type == 'delisting':
            item = apis.taobao_item_get(num_iid=task.num_iid,session=user.top_session)

            if item.has_key('item_get_response') and item['item_get_response'].has_key('item') :

                if item['item_get_response']['item']['approve_status'] == 'onsale':

                    response = apis.taobao_item_update_delisting\
                            (num_iid=task.num_iid,session=user.top_session)

            else :
                success = False
                logger.warn('Get item unsuccess: %s'%item)

        if response.has_key('error_response'):
            logger.error('Executing updateItemListTask(task_id:%s) errorresponse:%s' %(task.task_id,response))
            success = False

    except Exception,exc:
        success = False
        logger.error('Executing ItemListTask(id:%s) error:%s' %(task_id,exc), exc_info=True)
        if not settings.DEBUG:
            create_comment.retry(exc=exc,countdown=1)

    if success:
        task.status = 'success'
    else:
        task.status = 'execerror'

    task.save()


@task()
def updateAllItemListTask():

    currenttime = time.time()

    timeago = datetime.datetime.fromtimestamp\
            (currenttime - settings.EXECUTE_RANGE_TIME)
    timefuture = datetime.datetime.fromtimestamp\
            (currenttime + settings.EXECUTE_RANGE_TIME)

    tasks = ItemListTask.objects.filter\
            (update_time__gt=timeago,update_time__lt=timefuture,status='unexecute')

    for task in tasks:

        subtask(updateItemListTask).delay(task.id)




