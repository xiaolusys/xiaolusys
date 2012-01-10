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
from shopback.task.models import ItemTask
from auth.utils import getSignatureTaoBao
from auth import apis
import logging

logger = logging.getLogger('updateitem')

@task()
def updateItemList(task_id,num_iid,num,session_key):

    try:
        session = SessionStore(session_key=session_key)
        top_parameters = session['top_parameters']
        expires_time = top_parameters['expires_in']
        timestamp = top_parameters['ts']

        if int(expires_time)+int(timestamp) < time.time():
            params = {
                'appkey':settings.APPKEY,
                'refresh_token':top_parameters['refresh_token'],
                'sessionkey':session['top_session']
            }
            sign_result = getSignatureTaoBao(params,settings.APPSECRET,both_side=False)
            params['sign'] = sign_result
            refresh_url = '%s?%s'%(settings.REFRESH_URL,urllib.urlencode(params))

            req = urllib2.urlopen(refresh_url)
            content = req.read()
            params = json.loads(content)

            session['top_session'] = params.get('top_session',None)
            session['top_parameters']['re_expires_id'] = params.get('re_expires_id',None)
            session['top_parameters']['expires_in'] = params.get('expires_id',None)
            session['top_parameters']['refresh_token'] = params.get('refresh_token',None)
            session.save()

        task = ItemTask.objects.get(pk=task_id,status=True,is_success=False)

        item = apis.taobao_item_get(num_iid=num_iid,session=session.get('top_session',None))

        if item.has_key('item_get_response') and item['item_get_response'].has_key('item') :

            if item['item_get_response']['item']['approve_status'] == 'onsale':

                del_ret = apis.taobao_item_update_delisting(num_iid=num_iid,session=session.get('top_session',None))
                if del_ret.get('item_update_delisting_response',None) and \
                    del_ret['item_update_delisting_response'].get('item',None):
                    task.is_active = True
                else :
                    logger.warn('Delete itemlist unsuccess: %s'%update_ret,exc_info=True)
        else :
            logger.warn('Get item unsuccess: %s'%update_ret,exc_info=True)


        update_ret = apis.taobao_item_update_listing(num_iid,num,session.get('top_session',None))

        if update_ret.get('item_update_listing_response',None) and\
           update_ret['item_update_listing_response'].get('item',None):
            task.is_success = True
        else :
            logger.warn('Update itemlist unsuccess: %s'%update_ret,exc_info=True)

        task.save()

    except Exception,exc:
        print '%s'%exc
        logger.error('Executing ItemTask(id:%s) error:%s' %(task_id,exc), exc_info=True)





@task()
def updateAllItemTask():

    currenttime = time.time()
    timeago = datetime.datetime.fromtimestamp(currenttime - settings.EXECUTE_INTERVAL_TIME/2+60)
    timefuture = datetime.datetime.fromtimestamp(currenttime + settings.EXECUTE_INTERVAL_TIME/2+60)

    tasks = ItemTask.objects.filter(update_time__gt=timeago,update_time__lt=timefuture,status=True,is_success=False)

    for task in tasks:
        subtask(updateItemList).delay(task.id,task.num_iid,task.num,task.session_key)



