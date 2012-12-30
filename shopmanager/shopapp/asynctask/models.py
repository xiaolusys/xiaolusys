#-*- encoding:utf8 -*-
from django.db import models

TASK_CREATED  = 'CREATED'
TASK_ASYNCOK    = 'ASYNCOK'
TASK_ASYNCCOMPLETE = 'ASYNCCOMPLETE'
TASK_DOWNLOAD   = 'DOWNLOAD'
TASK_SUCCESS    = 'SUCCESS'
TASK_INVALID    = 'INVALID'

TAOBAO_ASYNC_TASK_STATUS =(
    (TASK_CREATED,'任务已创建'),
    (TASK_ASYNCOK,'淘宝异步任务请求成功'),
    (TASK_ASYNCCOMPLETE,'淘宝异步任务完成'),
    (TASK_DOWNLOAD,'异步任务结果已下载本地'),
    (TASK_SUCCESS,'任务已完成'),
    (TASK_INVALID,'任务已作废'),
)

class TaobaoAsyncTask(models.Model):
    #淘宝异步任务处理MODEL
    task_id  = models.AutoField(primary_key=True)
    task = models.TextField(max_length=256,blank=True)
    
    top_task_id = models.CharField(max_length=128,db_index=True,blank=True)
    user_id  = models.CharField(max_length=64,blank=True)
    
    result   = models.TextField(max_length=2000,blank=True)
    fetch_time  = models.DateField(null=True,blank=True)
    file_path_to = models.TextField(max_length=256,blank=True)
    
    create   = models.DateField(auto_now=True)
    modified = models.DateField(auto_now_add=True)
    status   = models.CharField(max_length=32,choices=TAOBAO_ASYNC_TASK_STATUS,default=TASK_CREATED)
    
    params   = models.CharField(max_length=1000,blank=True,null=True)
    class Meta:
        db_table = 'shop_taobao_asynctask'
        
        