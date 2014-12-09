# -*- coding:utf8 -*-
import re
import urllib
import httplib2
from BeautifulSoup import BeautifulSoup
from celery import Task
from celery.task import task
from celery.task.sets import subtask
from .models import SaleProduct, SaleSupplier, SaleCategory

ZHE_ITEM_NO_RE = re.compile('^.+ze(?P<item_no>[0-9]{16,22})')
TMALL_ITEM_ID_RE = re.compile('^.+id=(?P<item_id>[0-9]{6-16})')

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
        
        if str(response['status']).strip()  != '200':
            raise Exception(u'HTTP %s Error'%response['status'] )
        
        return BeautifulSoup(content)
        
        
class CrawZhe800ItemsTask(CrawTask):
    
    craw_urls = (('http://www.zhe800.com/zhuanchang/muying',u'母婴'),
                            ('http://www.zhe800.com/ju_tag/taofushi',u'女装'))
    
    
    def saveZ800Item(self,item_url,category=''):
        
        zsoup = self.getBeaSoupByCrawUrl(item_url)
        
        bname_tags = zsoup.findAll(attrs={'class' : 'nubB bm'})
        if not bname_tags:
            return

        outer_id = ZHE_ITEM_NO_RE.match(item_url).groupdict().get('item_no')
        sproduct,state = SaleProduct.objects.get_or_create(outer_id=outer_id)
        if sproduct.title:
            return
        
        brand_name = bname_tags[0].findAll('p')[0].text
        supplier,state =  SaleSupplier.objects.get_or_create(supplier_name=brand_name)
        salecategory,state   = SaleCategory.objects.get_or_create(name=category)
        title    = zsoup.findAll(attrs={'class':'detailmeta r'})[0].findAll('h1')[0].text.strip()
        item_pic = zsoup.findAll(attrs={'class':'deteilpic l'})[0].findAll('img')[0].attrMap.get('src','')
        price  = zsoup.findAll(attrs={'class':'nubA clear'})[0].findAll('i')[0].text.strip()
        
        sproduct.title = title
        sproduct.price = price
        sproduct.pic_url = item_pic
        sproduct.product_link = item_url
        sproduct.sale_supplier = supplier
        sproduct.sale_category = salecategory
        sproduct.platform = SaleProduct.ZHEBABAI
        sproduct.save()
        
        
    def saveTaobaoItem(self,item_url,category=''):
        
        tsoup = self.getBeaSoupByCrawUrl(item_url)
        
        bname_tags = tsoup.findAll(attrs={'class' : 'shop-intro'})
        if not bname_tags:
            return

        outer_id = TMALL_ITEM_ID_RE.match(item_url).groupdict().get('item_id')
        sproduct,state = SaleProduct.objects.get_or_create(outer_id=outer_id)
        if sproduct.title:
            return
        
        brand_name = bname_tags[0].findAll('shopLink')[0].text
        supplier,state =  SaleSupplier.objects.get_or_create(supplier_name=brand_name)
        salecategory,state   = SaleCategory.objects.get_or_create(name=category)
        title          = tsoup.findAll(attrs={'class':'tb-detail-hd'})[0].findAll('h1')[0].text.strip()
        item_pic = tsoup.findAll(attrs={'class':'ks-imagezoom-wrap'})[0].findAll('img')[0].attrMap.get('src','')
        price        = tsoup.findAll(attrs={'class':'tm-promo-price'})[0].findAll('tm-price')[0].text.strip()
        
        sproduct.title = title
        sproduct.price = price
        sproduct.pic_url = item_pic
        sproduct.product_link = item_url
        sproduct.sale_supplier = supplier
        sproduct.sale_category = salecategory
        sproduct.platform = SaleProduct.TAOBAO
        sproduct.save()
            
    
    def crawItems(self,brand_url,category=''):
        
        isoup = self.getBeaSoupByCrawUrl(brand_url)
        item_tags  = isoup.findAll(attrs={'href' : re.compile("^http://shop.zhe800.com/products/ze[\w]+")})
        for item_tag in item_tags:
            item_url = item_tag.attrMap.get('href','')
            if not item_url :
                continue
            self.saveZ800Item(item_url,category=category)
                         
        tmall_tags = isoup.findAll(attrs={'href' : re.compile("^http://detail.tmall.com/item.htm?")})
        for tmall_tag in tmall_tags:
            tmall_url = tmall_tag.attrMap.get('href','')
            if not tmall_url :
                continue
            self.saveTaobaoItem(tmall_url,category=category)
        
    
    def crawBrands(self,url,category=''):
        
        brand_url_set = set([])
        has_next = True
        page         = 1
        
        while has_next:
                    
            zhe_url              = '%s?%s'%(url,urllib.urlencode({'page':page,'sort':'hottest','type':'all'}))
            bsoup = self.getBeaSoupByCrawUrl(zhe_url)
            print zhe_url
            brand_tags = bsoup.findAll(attrs={'href' : re.compile("^http://brand.zhe800.com/[\w]+")})
            for brand_tag in brand_tags:
                
                brand_url = brand_tag.attrMap.get('href','')
                if not brand_url or brand_url in brand_url_set:
                    continue
                brand_url_set.add(brand_url)
                self.crawItems(brand_url,category=category)
                
            item_tags  = bsoup.findAll(attrs={'href' : re.compile("^http://shop.zhe800.com/products/ze[\w]+")})
            for item_tag in item_tags:
                item_url = item_tag.attrMap.get('href','')
                if not item_url :
                    continue
                self.saveZ800Item(item_url,category=category)
                         
            tmall_tags = bsoup.findAll(attrs={'href' : re.compile("^http://detail.tmall.com/item.htm?")})
            for tmall_tag in tmall_tags:
                tmall_url = tmall_tag.attrMap.get('href','')
                if not tmall_url :
                    continue
                self.saveTaobaoItem(tmall_url,category=category)
            print item_tags,'-----------',tmall_tags
            if not item_tags or not tmall_tags:
                has_next = False
            has_next = False

    def run(self,*args, **kwargs):
        
        for craw_url,category_name in self.craw_urls:
            self.crawBrands(craw_url,category= category_name)
     
     
class CrawXiaoherItemsTask(CrawTask):
    
    craw_url =  (('http://www.zhe800.com/ju_tag/taomuying',u'母婴'),
                            ('http://www.zhe800.com/ju_tag/taofushi',u'女装'))
    
    def run(self,*args, **kwargs):
         pass
     
     