# -*- coding:utf8 -*-
from celery import Task
from celery.task import task
from celery.task.sets import subtask
from .models import SaleProduct, SaleSupplier, SaleCategory

class CrawZhe800ItemsTask(Task):
    
    craw_urls = (('http://www.zhe800.com/ju_tag/taomuying',u'母婴'),
                            ('http://www.zhe800.com/ju_tag/taofushi',u'女装'))
    platform  = SaleProduct.ZHEBABAI
    
    def crawUrlItems(self,url):
        pass
        
    
    def run(self,*args, **kwargs):
        pass
     
     
class CrawXiaoherItemsTask(Task):
    
    craw_url =  (('http://www.zhe800.com/ju_tag/taomuying',u'母婴'),
                            ('http://www.zhe800.com/ju_tag/taofushi',u'女装'))
    platform  = SaleProduct.XIAOHER
    
    def run(self,*args, **kwargs):
         pass
     
     