# -*- coding:utf8 -*-
import re
import httplib2
from BeautifulSoup import BeautifulSoup
from celery import Task
from celery.task import task
from celery.task.sets import subtask
from .models import SaleProduct, SaleSupplier, SaleCategory


class CrawTask(Task):
    
    def getBeaSoupByCrawUrl(self,url):
        headers = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
               'Accept-Encoding':'gzip,deflate,sdch',
               'Accept-Language':'en-US,en;q=0.8',
               'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.75 Safari/535.7'
            }
        http = httplib2.Http()
        response,content = http.request(url,'GET',headers=headers)
        
        if response['status']  != 200:
            raise Exception(u'HTTP %s Error'%response['status'] )
        
        return BeautifulSoup(content)
        
        
class CrawZhe800ItemsTask(CrawTask):
    
    craw_urls = (('http://www.zhe800.com/zhuanchang/muying',u'母婴'),
                            ('http://www.zhe800.com/ju_tag/taofushi',u'女装'))
    platform  = SaleProduct.ZHEBABAI
    
    def crawItems(self):
        pass
    
    def crawBrands(self,url,category=''):
        
        brand_url_set = set([])
        soup = self.getBeaSoupByCrawUrl(url)
        brand_tags = soup.findAll(attrs={'href' : re.compile("^http://brand.zhe800.com/[\w]+")})
        
        for brand_tag in brand_tags:
            
            brand_url = brand_tag
            if brand_url in brand_url_set:
                continue
            brand_url_set.add(brand_url)
            

         
        
    
    def run(self,*args, **kwargs):
        
        for craw_url,category_name in self.craw_urls:
            self.crawBrands(craw_url, category_name)
     
     
class CrawXiaoherItemsTask(CrawTask):
    
    craw_url =  (('http://www.zhe800.com/ju_tag/taomuying',u'母婴'),
                            ('http://www.zhe800.com/ju_tag/taofushi',u'女装'))
    platform  = SaleProduct.XIAOHER
    
    def run(self,*args, **kwargs):
         pass
     
     