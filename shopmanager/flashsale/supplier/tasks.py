# -*- coding:utf8 -*-
import os
import re
import zlib
import cookielib
import datetime
import urllib,urllib2
from BeautifulSoup import BeautifulSoup
from celery import Task
from celery.task import task
from celery.task.sets import subtask
from .models import SaleProduct, SaleSupplier, SaleCategory
import logging

logger = logging.getLogger('celery.handler')


ZHE_ITEM_NO_RE     = re.compile('^.+ze(?P<item_no>[0-9]{16,22})')
TMALL_ITEM_ID_RE = re.compile('^.+id=(?P<item_id>[0-9]{6,16})')
XHER_ITEM_ID_RE    = re.compile('^.+/[0-9]+/(?P<item_id>[0-9]{6,16})')
ENCODING_RE          = re.compile('^.+charset=(?P<encoding>[\w]+)')

ckjar = cookielib.MozillaCookieJar(os.path.join('/tmp/', 'cookies.txt'))

class CrawTask(Task):
    
    def getBeaSoupByCrawUrl(self,url):
        headers = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Encoding':'gzip,deflate',
               'Accept-Language':'en-US,en;q=0.8',
               'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0',
               'Referer':'http://www.zhe800.com',
               'Connection':'keep-alive'}
        
        request = urllib2.Request(url)
        for k,v in headers.iteritems():
            request.add_header(k,v)
            
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(ckjar))
        response = opener.open(request)
        
        if str(response.code).strip()  != '200':
            raise Exception(u'HTTP %s Error'%response.code )
        
        html = response.read()
        gzipped = response.headers.get('Content-Encoding')
        if gzipped:
            html = zlib.decompress(html, 16+zlib.MAX_WBITS)
            
        coding_str = response.headers.get('Content-Type')
        
        en_match = ENCODING_RE.match(coding_str)
        encoding = en_match and en_match.groupdict().get('encoding','utf-8') or 'gbk'

        return BeautifulSoup(html.decode(encoding)),response
        
        
class CrawZhe800ItemsTask(CrawTask):
    
    category_urls = (('http://www.zhe800.com/zhuanchang/muying',u'母婴'),
                                    ('http://www.zhe800.com/ju_tag/taofushi',u'女装'),)

    imatch_urls = ("^http://shop.zhe800.com/products/ze",
                                "^http://detail.tmall.com/item.htm",
                                "^http://item.taobao.com/item.htm",
                                "^http://out.zhe800.com/ju/deal/",)
    
    imatch_re = re.compile('(%s)'%'|'.join(imatch_urls))
    
    def saveZ800Item(self,zsoup,item_url,category=''):

        outer_id = ZHE_ITEM_NO_RE.match(item_url).groupdict().get('item_no')
        sproduct,state = SaleProduct.objects.get_or_create(outer_id=outer_id)
        if sproduct.title:
            return
        
        bname_tags = zsoup.findAll(attrs={'class' : 'nubB bm'})
        if not bname_tags:
            return
        
        brand_name = bname_tags[0].findAll('p')[0].text.strip()
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
        
        
    def saveTmallItem(self,tsoup,item_url,category=''):
        
        outer_id = TMALL_ITEM_ID_RE.match(item_url).groupdict().get('item_id')
        sproduct,state = SaleProduct.objects.get_or_create(outer_id=outer_id)
        if sproduct.title:
            return
        
        bname_tags = tsoup.findAll(attrs={'class' : 'slogo-shopname'})
        if not bname_tags:
            return
        
        brand_name = bname_tags[0].findAll('strong')[0].text.strip()
        supplier,state =  SaleSupplier.objects.get_or_create(supplier_name=brand_name)
        salecategory,state   = SaleCategory.objects.get_or_create(name=category)
        title          = tsoup.findAll(attrs={'class':'tb-detail-hd'})[0].findAll('h1')[0].text.strip()
        item_pic = tsoup.findAll(attrs={'class':'tb-booth'})[0].findAll('img')[0].attrMap.get('src','')
        price        = tsoup.findAll(attrs={'class':'tm-promo-price'}) or 0
        if price:
            price = price[0].findAll(attrs={'class':'tm-price'})[0].text.strip()
        
        sproduct.title = title
        sproduct.price = price
        sproduct.pic_url = item_pic
        sproduct.product_link = item_url
        sproduct.sale_supplier = supplier
        sproduct.sale_category = salecategory
        sproduct.platform = SaleProduct.TMALL
        sproduct.save()
            
    def saveTaobaoItem(self,tsoup,item_url,category=''):
        
        outer_id = TMALL_ITEM_ID_RE.match(item_url).groupdict().get('item_id')
        sproduct,state = SaleProduct.objects.get_or_create(outer_id=outer_id)
        if sproduct.title:
            return
        
        bname_tags = tsoup.findAll(attrs={'class' : 'tb-seller-name'})
        if not bname_tags:
            return
        
        brand_name = bname_tags[0].text.strip()
        supplier,state =  SaleSupplier.objects.get_or_create(supplier_name=brand_name)
        salecategory,state   = SaleCategory.objects.get_or_create(name=category)
        title          = tsoup.findAll(attrs={'class':'tb-main-title'})[0].text.strip()
        item_pic = tsoup.findAll(attrs={'id':'J_ImgBooth'})[0].attrMap.get('data-src','')
        price        = tsoup.findAll(attrs={'id':'J_Price'}) or 0
        if price:
            price = price[0].text.strip()
        
        sproduct.title = title
        sproduct.price = price
        sproduct.pic_url = item_pic
        sproduct.product_link = item_url
        sproduct.sale_supplier = supplier
        sproduct.sale_category = salecategory
        sproduct.platform = SaleProduct.TAOBAO
        sproduct.save()
    
    def crawItemUrl(self,soup,category=''):
        
        item_tags  = soup.findAll(attrs={'href' : self.imatch_re})
        
        for item_tag in item_tags:
            try:
                item_url = item_tag.attrMap.get('href','')
                isoup,response     = self.getBeaSoupByCrawUrl(item_url)
                resp_url = response.geturl()
              
                if  resp_url.startswith('http://shop.zhe800.com/products/'):
                    self.saveZ800Item(isoup, resp_url, category=category)
                 
                if  resp_url.startswith('http://detail.tmall.com/item.htm'):
                    self.saveTmallItem(isoup, resp_url, category=category)
                    
                if  resp_url.startswith('http://item.taobao.com/item.htm'):
                    self.saveTaobaoItem(isoup, resp_url, category=category)
            except Exception,exc:
                logger.error('ITEM URL ERROR:%s'%exc.message,exc_info=True)
                
        return len(item_tags)
    
    def crawItems(self,brand_url,category=''):
        
        print 'DEBUG BRAND:',datetime.datetime.now(),brand_url
        isoup,response = self.getBeaSoupByCrawUrl(brand_url)
        self.crawItemUrl(isoup, category=category)
    
    def getPageUrl(self,url,page):
        
        if url.startswith('http://www.zhe800.com/ju_tag/taofushi'):
            return url+'/page/%s'%page
        
        if url.startswith('http://www.zhe800.com/zhuanchang/muying'):
            return '%s?%s'%(url,urllib.urlencode({'page':page,'sort':'hottest','type':'all'}))
        return url
    
    def crawBrands(self,url,category=''):
        
        brand_url_set = set([])
        has_next = True
        page         = 1
        while has_next:
                    
            zhe_url    = self.getPageUrl(url, page)
            bsoup,response = self.getBeaSoupByCrawUrl(zhe_url)
            
            brand_tags = bsoup.findAll(attrs={'href' : re.compile("(^http://brand.zhe800.com/[\w]+|^http://www.zhe800.com/zhuanchang/[\w]+)")})
            for brand_tag in brand_tags:
                
                brand_url = brand_tag.attrMap.get('href','')
                if  brand_url in brand_url_set:
                    continue

                brand_url_set.add(brand_url)
                self.crawItems(brand_url,category=category)
            
            item_num = self.crawItemUrl(bsoup, category=category)
            page += 1
            
            if not item_num :
                has_next = False

    def run(self,*args, **kwargs):
        
        for craw_url,category_name in self.category_urls:
            self.crawBrands(craw_url,category= category_name)
     
#############################################################     
class CrawXiaoherItemsTask(CrawTask):
    
    category_urls =  (('http://www.xiaoher.com/?q=children',u'母婴'),
                                      ('http://www.xiaoher.com/?q=ladys',u'女装'),)
    
    site_url = 'http://www.xiaoher.com'
    
    def saveXiaoHerItem(self,tsoup,item_url,category=''):
        
        outer_id = XHER_ITEM_ID_RE.match(item_url).groupdict().get('item_id')
        sproduct,state = SaleProduct.objects.get_or_create(outer_id=outer_id)
        if sproduct.title:
            return
        
        bname_tags = tsoup.findAll(attrs={'class' : 'detail_head'})
        if not bname_tags:
            return
        
        brand_name = bname_tags[0].findAll(attrs={'href':re.compile('^/show/')})[0].text.strip()
        supplier,state =  SaleSupplier.objects.get_or_create(supplier_name=brand_name)
        salecategory,state   = SaleCategory.objects.get_or_create(name=category)
        title          = tsoup.findAll(attrs={'class':'details clearfix'})[0].findAll('h2')[0].text.strip()
        item_pic = tsoup.findAll(attrs={'class':'bigPic'})[0].findAll('img')[0].attrMap.get('src','')
        price        = tsoup.findAll(attrs={'class':'item price'})[0].findAll('span')[0].text.replace(u'￥','')
         
        sproduct.title = title
        sproduct.price = price
        sproduct.pic_url = item_pic
        sproduct.product_link = item_url
        sproduct.sale_supplier = supplier
        sproduct.sale_category = salecategory
        sproduct.platform = SaleProduct.XIAOHER
        sproduct.save()
    
    def crawItemUrl(self,soup,category=''):
        
        item_tags  = soup.findAll(attrs={'href' : re.compile('^/detail/[0-9]+/[0-9]+')})
        for item_tag in item_tags:
            try:
                item_url = '%s%s'%(self.site_url,item_tag.attrMap.get('href',''))
                isoup,response     = self.getBeaSoupByCrawUrl(item_url)
                resp_url = response.geturl()
              
                self.saveXiaoHerItem(isoup, resp_url, category=category)
            except Exception,exc:
                logger.error('ITEM URL ERROR:%s'%exc.message,exc_info=True)
                
        return len(item_tags)
    
    def crawItems(self,brand_url,category=''):
        
        print 'DEBUG BRAND:',datetime.datetime.now(),brand_url
        isoup,response = self.getBeaSoupByCrawUrl(brand_url)
        self.crawItemUrl(isoup, category=category)
    
    def getPageUrl(self,url,page):
        
        return url
    
    def crawBrands(self,url,category=''):
        
        brand_url_set = set([])
        has_next = True
        page         = 1
        while has_next:
                    
            zhe_url    = self.getPageUrl(url, page)
            bsoup,response = self.getBeaSoupByCrawUrl(zhe_url)
            
            brand_tags = bsoup.findAll(attrs={'href' : re.compile("^/show/[0-9]+")})
            for brand_tag in brand_tags:
                
                brand_url = '%s%s'%(self.site_url,brand_tag.attrMap.get('href',''))
                if  brand_url in brand_url_set:
                    continue
                
                brand_url_set.add(brand_url)
                self.crawItems(brand_url,category=category)
            
            item_num = self.crawItemUrl(bsoup, category=category)
            has_next = False

    def run(self,*args, **kwargs):
        
        for craw_url,category_name in self.category_urls:
            self.crawBrands(craw_url,category= category_name)
     
     
