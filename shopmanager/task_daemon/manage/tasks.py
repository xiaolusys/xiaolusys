import datetime
import time
import json
import urllib
import urllib2
from celery.task import task
from celery.task.sets import subtask
from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from shopback.task.models import ItemTask
from auth.utils import getSignatureTaoBao,refresh_session
from auth import apis
import logging

logger = logging.getLogger('updateitem')

@task()
def updateItemList(task_id,num_iid,num,session_key):

    try:
        session = SessionStore(session_key=session_key)

        refresh_success = refresh_session(session.settings)

        if refresh_success:
            session.save()

        task = ItemTask.objects.get(pk=task_id,status=True,is_success=False)

        if task.task_type == 1:

            update_ret = apis.taobao_item_update_listing(num_iid,num,session.get('top_session',None))

            if update_ret.get('item_update_listing_response',None) and\
               update_ret['item_update_listing_response'].get('item',None):
                task.is_success = True
            else :
                logger.warn('Update itemlist unsuccess: %s'%update_ret)
        else:
            item = apis.taobao_item_get(num_iid=num_iid,session=session.get('top_session',None))

            if item.has_key('item_get_response') and item['item_get_response'].has_key('item') :

                if item['item_get_response']['item']['approve_status'] == 'onsale':

                    del_ret = apis.taobao_item_update_delisting(num_iid=num_iid,session=session.get('top_session',None))
                    if del_ret.get('item_update_delisting_response',None) and \
                        del_ret['item_update_delisting_response'].get('item',None):
                        task.is_success = True
                    else :
                        logger.warn('Delete itemlist unsuccess: %s'%del_ret)
            else :
                logger.warn('Get item unsuccess: %s'%item)

        task.save()

    except Exception,exc:
        logger.error('Executing ItemTask(id:%s) error:%s' %(task_id,exc), exc_info=True)



@task()
def updateAllItemTask():

    currenttime = time.time()
    timeago = datetime.datetime.fromtimestamp(currenttime - settings.EXECUTE_RANGE_TIME)
    timefuture = datetime.datetime.fromtimestamp(currenttime + settings.EXECUTE_RANGE_TIME)

    tasks = ItemTask.objects.filter(update_time__gt=timeago,update_time__lt=timefuture,status=True,is_success=False)

    for task in tasks:

        subtask(updateItemList).delay(task.id,task.num_iid,task.num,task.session_key)




