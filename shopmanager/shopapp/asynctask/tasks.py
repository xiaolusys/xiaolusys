#-*- encoding:utf8 -*-
import sys
import os
import string
import zipfile 
import types
import hashlib
import re
import datetime
import json
import urllib2
from os.path import basename
from urlparse import urlsplit
from django.conf import settings
from django.core.cache import cache
from celery.task import task,Task
from celery.registry import tasks
from celery.app.task import BaseTask
from celery.signals import task_prerun
from shopback.base.exception import NotImplement
from shopapp.asynctask.models import TaobaoAsyncTask,TASK_ASYNCOK,TASK_INVALID,TASK_CREATED,TASK_SUCCESS,\
    TASK_ASYNCCOMPLETE,TASK_DOWNLOAD
from shopback.monitor.models import SystemConfig
from shopback.categorys.models import Category
from shopback.orders.models import Trade
from auth import apis
import logging

logger = logging.getLogger('asynctask.handler')

TASK_STATUS ={
    'new':TASK_ASYNCOK,          
    'done':TASK_ASYNCCOMPLETE,
    'fail':TASK_INVALID,
    'doing':TASK_ASYNCOK              
}

@task()
def taobaoAsyncHandleTask():
    """ 淘宝异步任务处理核心类 """
    asynctasks = TaobaoAsyncTask.objects.filter(status__in=(TASK_ASYNCOK,TASK_ASYNCCOMPLETE,TASK_DOWNLOAD))
    for asynctask in asynctasks:
        task_name = asynctask.task

        if not task_name:
            continue
        task_handler = tasks[task_name.groupdict()['task_name']]
        if asynctask.status == TASK_ASYNCOK:
            task_handler.is_taobao_complete(asynctask.task_id)
            asynctask = TaobaoAsyncTask.objects.get(task_id=asynctask.task_id)
            
        if asynctask.status == TASK_ASYNCCOMPLETE:
            task_handler.download_result_file(asynctask.task_id)
            
            asynctask = TaobaoAsyncTask.objects.get(task_id=asynctask.task_id)
                
        if asynctask.status == TASK_DOWNLOAD:
            handlerresult = task_handler.handle_result_file(asynctask.task_id)
            if handlerresult:
                TaobaoAsyncTask.objects.filter(task_id=asynctask.task_id).update(status=TASK_SUCCESS)



class TaobaoAsyncBaseTask(Task):
    """
        {
            "topats_itemcats_get_response": {
                "task": {
                    "download_url": "http://download.api.taobao.com/download?id=bacnoiewothoi",
                    "check_code": "efdbe2545a01aff317f0cbaad6663c7c",
                    "schedule": "2000-01-01 00:00:00",
                    "task_id": 12345,
                    "status": "done",
                    "method": "taobao.topats.trades.fullinfo.get",
                    "created": "2000-01-01 00:00:00"
                }
            }
        }
    """
    
    def run(self,*args,**kwargs):
        raise NotImplement("该方法没有实现")
    
    def after_return(self,status,result_dict,*args,**kwargs):

        try:
            async_task = TaobaoAsyncTask.objects.create(task=self.__class__.__name__) 
        except Exception,exc:
            raise
        else:
            user_id     = result_dict['user_id']
            next_status = TASK_ASYNCOK if result_dict['success'] else TASK_INVALID
            result_json = json.dumps(result_dict['result']) if result_dict['success'] else result_dict['result']
            top_task_id = result_dict.get('top_task_id','')
            params      = json.dumps(result_dict.get('params',{}))
            TaobaoAsyncTask.objects.filter(task_id=async_task.task_id)\
                .update(user_id=user_id,status=next_status,result=result_json,top_task_id=top_task_id,params=params)
         
         
    def is_taobao_complete(self,task_id): 
        try:
            async_task = TaobaoAsyncTask.objects.get(task_id=task_id)
        except:
            logger.error('the taobao async task(id:%s) is not exist'%task_id)
        else:
            try:
                response = apis.taobao_topats_result_get(task_id=async_task.top_task_id,tb_user_id=async_task.user_id)
            except Exception,exc:
                logger.error(exc.message,exc_info=True)
            else:
                task_status = response['topats_result_get_response']['task']['status'] 
                async_task_status = TASK_STATUS.get(task_status,TASK_INVALID) 
                TaobaoAsyncTask.objects.filter(task_id=task_id).update(status=async_task_status,result=json.dumps(response))
    
      
    def download_result_file(self,task_id):

        try:
            async_task = TaobaoAsyncTask.objects.get(task_id=task_id)
        except:
            logger.error('the taobao async task(id:%s) is not exist'%task_id)
        else:
            result = json.loads(async_task.result)
            task = result['topats_result_get_response']['task']
            check_code = task['check_code']
            download_url = task['download_url']
            file_path  = os.path.join(settings.ASYNC_FILE_PATH,task['method'],str(task['task_id']))
            try:
                self.dirCreate(file_path)
                success = self.download_file(download_url,check_code,file_path=file_path)
            except Exception,exc:
                logger.error('%s'%exc,exc_info=True)
            else:
                async_status = TASK_DOWNLOAD if success else TASK_ASYNCOK
                TaobaoAsyncTask.objects.filter(task_id=task_id).update(status=async_status,file_path_to=file_path)
    
    
    def handle_result_file(self,task_id,result={}):
        raise NotImplement("该方法没有实现")
    
    def url2name(self,url):
        return basename(urlsplit(url)[2])

    def dirCreate(self,dir): 
        if not os.path.exists(dir): 
            os.makedirs(dir)
    
    def download_file(self,url,valid_code,file_path=None):
        fileName = self.url2name(url)
        req = urllib2.Request(url)
        r = urllib2.urlopen(req)
        content = r.read()
        
        if valid_code != hashlib.md5(content).hexdigest():
            return False
        
        if r.info().has_key('Content-Disposition'):
            # If the response has Content-Disposition, we take file name from it
            fileName = r.info()['Content-Disposition'].split('filename=')[1]
            if fileName[0] == '"' or fileName[0] == "'":
                fileName = fileName[1:-1]
        elif r.url != url:
            # if we were redirected, the real file name we take from the final URL
            fileName = url2name(r.url)
        if file_path:
            # we can force to save the file as specified name
            fileName = os.path.join(file_path,fileName)
   
        with open(fileName, 'wb') as f:
            f.write(content)
        try:
            z = zipfile.ZipFile(fileName,'r')
            for zf in z.namelist(): 
                fname = os.path.join(file_path, zf)
                if fname.endswith('/'):
                    fname = string.rstrip(fname,'/')
                    if not os.path.exists(fname):
                        os.mkdir(fname)
                        continue              
                #if sys.platform == 'win32':
                #    fname = string.replace(fname, '/', '\\')
                file(fname, 'wb').write(z.read(zf))
        except Exception,exc:
             logger.error('%s'%exc,exc_info=True)
             return False
        else:   
            os.remove(fileName)
            
        return True
        
        
#========================== Async Category Task ============================
class AsyncCategoryTask(TaobaoAsyncBaseTask): 
    
    def run(self,cids,user_id,seller_type='B',fetch_time=None,*args,**kwargs):

        try:
            response = apis.taobao_topats_itemcats_get(seller_type=seller_type,cids=cids,tb_user_id=user_id)
        except Exception,exc:
            logger.error('%s'%exc,exc_info=True)
            return {'user_id':user_id,'success':False,'result':'%s'%exc} 
        else:
            top_task_id =response['topats_itemcats_get_response']['task']['task_id']
            return {'user_id':user_id,
                    'success':True,
                    'result':response,
                    'top_task_id':top_task_id,
                    'params':{'cids':cids,'seller_type':seller_type}}

 
    def handle_result_file(self,task_id):
        try:
            async_task = TaobaoAsyncTask.objects.get(task_id=task_id)
            task_files = os.listdir(async_task.file_path_to) 
            for fname in task_files:
                fname = os.path.join(async_task.file_path_to,fname)
                with open(fname,'r') as f:
                    content = f.read()
                content = json.loads(content)
                self.save_category(content)
            return True
        except Exception,exc:
            logger.error('async task result handle fail: %s'%exc,exc_info=True)
            return False        
            
    def save_category(self,cat_json):
        cat,state = Category.objects.get_or_create(cid=cat_json['cid'])
        cat.parent_cid = cat_json['parentCid']  
        cat.is_parent  = cat_json['isParent'] 
        cat.name       = cat_json['name'] 
        cat.sortOrder  = cat_json['sortOrder']   
        cat.save()
        
        sub_cat_jsons = cat_json['childCategoryList']  
        if isinstance(sub_cat_jsons,(list,tuple)):
            for sub_cat_json in sub_cat_jsons:
                self.save_category(sub_cat_json)

tasks.register(AsyncCategoryTask) 
  

#================================ Async Order Task   ==================================
class AsyncOrderTask(TaobaoAsyncBaseTask): 
    
    def run(self,start_time,end_time,user_id,fetch_time=None,*args,**kwargs):

        if start_time>end_time:
            return 
        
        start_time = start_time.strftime("%Y%m%d")
        end_time   = end_time.strftime("%Y%m%d")
        try:
            response = apis.taobao_topats_trades_sold_get(start_time=start_time,end_time=end_time,tb_user_id=user_id)
            #response = {u'topats_trades_sold_get_response': {u'task': {u'task_id': 37606086, u'created': u'2012-08-31 17:40:42'}}}
        except Exception,exc:
            logger.error('%s'%exc,exc_info=True)
            return {'user_id':user_id,'success':False,'result':'%s'%exc} 
        else:
            top_task_id =response['topats_trades_sold_get_response']['task']['task_id']
            return {'user_id':user_id,
                    'success':True,
                    'result':response,
                    'top_task_id':top_task_id,
                    'params':{'start_time':start_time,'end_time':end_time}}

 
    def handle_result_file(self,task_id):
        try:
            async_task = TaobaoAsyncTask.objects.get(task_id=task_id)
            task_files = os.listdir(async_task.file_path_to) 
            for fname in task_files:
                fname = os.path.join(async_task.file_path_to,fname)
                with open(fname,'r') as f:
                    order_list = f.readlines()
                    
                for order_str in order_list:
                    order_dict = json.loads(order_str)
                    Trade.save_trade_through_dict(async_task.user_id,order_dict['trade_fullinfo_get_response']['trade'])
            
            return True        
        except Exception,exc:
            logger.error('async task result handle fail: %s'%exc,exc_info=True)
            return False
            
            

tasks.register(AsyncOrderTask) 







