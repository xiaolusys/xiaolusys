#-*- coding:utf8 -*-
import time
import datetime
import json
import urllib2
import cgi
from lxml import etree
from StringIO import StringIO
from celery.task import task
from celery.task.sets import subtask
from celery import Task


class NotifyReferalAwardTask(Task):
    
    max_retries  = 3
    
    def run(self,user_openid):
        
        from shopapp.weixin_sales.service import WeixinSaleService
            
        wx_service = WeixinSaleService(user_openid)
        
        wx_service.notifyReferalAward()
        
            
            
