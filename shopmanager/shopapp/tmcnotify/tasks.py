#-*- coding:utf8 -*-
from celery.task import task
from celery.task.sets import subtask
from celery import Task
from django.conf import settings


class ProcessMessageTask(Task):
    """ 处理消息 """
    
    
    def run(self,message):
        
        try:
            pass
        except:
            pass
    
    
class ProcessMessageCallBack(Task):
    """ 处理消息回调"""
    
    def run(self,message_status):
        
        try:
            pass
        except:
            pass    
        
    
