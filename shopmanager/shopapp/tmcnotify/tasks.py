#-*- coding:utf8 -*-
from celery.task import task
from celery.task.sets import subtask
from celery import Task
from django.conf import settings


class TMCMessageTask(Task):
    """ 获取TMC消息 """
    
    def __init__(self):
        self.item = None
        
    def run(self,num_iid):
        
        try:
            pass
        except:
            pass
    
    
    
        
    
