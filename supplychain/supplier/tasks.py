# -*- coding:utf8 -*-
import os
import re
import zlib
import cookielib
import datetime
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
from celery import Task
from celery.task import task
from celery.task.sets import subtask
from .models import SaleProduct, SaleSupplier, SaleCategory
import logging
from django.db.models import Sum
from supplychain.supplier.models import SupplierFigure
from supplychain.supplier.models.schedule import SaleProductManage
logger = logging.getLogger('celery.handler')

ZHE_ITEM_NO_RE = re.compile('^.+ze(?P<item_no>[0-9]{16,22})')
TMALL_ITEM_ID_RE = re.compile('^.+id=(?P<item_id>[0-9]{6,16})')
XHER_ITEM_ID_RE = re.compile('^.+/[0-9]+/(?P<item_id>[0-9]{6,16})')
VIP_ITEM_ID_RE = re.compile('^.+/detail-[0-9]+-(?P<item_id>[0-9]+).html')
JHS_ITEM_ID_RE = re.compile('^.+item_id=(?P<item_id>[0-9]{6,16})')
BBW_ITEM_ID_RE = re.compile('^.+/detail/(?P<item_id>[0-9]{6,16}).html')
ENCODING_RE = re.compile('^.+charset=(?P<encoding>[\w]+)')

ckjar = cookielib.MozillaCookieJar(os.path.join('/tmp/', 'cookies.txt'))


class CrawTask(Task):
    def getBeaSoupByCrawUrl(self, url):
        headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Encoding': 'gzip,deflate',
                   'Accept-Language': 'en-US,en;q=0.8',
                   'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0',
                   'Referer': 'http://www.zhe800.com',
                   'Connection': 'keep-alive'}

        request = urllib2.Request(url)
        for k, v in headers.iteritems():
            request.add_header(k, v)

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(ckjar))
        response = opener.open(request)

        if str(response.code).strip() != '200':
            raise Exception(u'HTTP %s Error' % response.code)

        html = response.read()
        gzipped = response.headers.get('Content-Encoding')
        if gzipped:
            html = zlib.decompress(html, 16 + zlib.MAX_WBITS)

        coding_str = response.headers.get('Content-Type')

        en_match = ENCODING_RE.match(coding_str)
        encoding = en_match and en_match.groupdict().get('encoding', 'utf-8') or 'utf8'

        return BeautifulSoup(html.decode(encoding)), response

    def getOrCreateSupplier(self, supplier_name, platform="", category=""):

        supplier, state = SaleSupplier.objects.get_or_create(supplier_name=supplier_name)
        if not supplier.platform or not supplier.category:
            supplier.platform = platform
            supplier.category = category
            supplier.save()

        return supplier


class CrawZhe800ItemsTask(CrawTask):
    category_urls = (('http://www.zhe800.com/zhuanchang/muying', u'母婴'),
                     ('http://www.zhe800.com/ju_tag/taofushi', u'女装'),
                     ('http://www.zhe800.com/ju_type/baoyou', u'9.9包邮'),)

    imatch_urls = ("^http://shop.zhe800.com/products/ze",
                   "^http://detail.tmall.com/item.htm",
                   "^http://item.taobao.com/item.htm",
                   "^http://out.zhe800.com/ju/deal/",)

    imatch_re = re.compile('(%s)' % '|'.join(imatch_urls))

    def saveZ800Item(self, zsoup, item_url, category='', **kwargs):

        outer_id = ZHE_ITEM_NO_RE.match(item_url).groupdict().get('item_no')
        sproduct, state = SaleProduct.objects.get_or_create(
            outer_id=outer_id,
            platform=SaleProduct.ZHEBABAI)

        bname_tags = zsoup.findAll(attrs={'class': 'nubB bm'})
        if not bname_tags:
            return

        brand_name = bname_tags[0].findAll('p')[0].text.strip()
        salecategory, state = SaleCategory.objects.get_or_create(name=category)

        supplier = self.getOrCreateSupplier(
            supplier_name=brand_name,
            platform=SaleProduct.ZHEBABAI,
            category=salecategory)

        title = zsoup.findAll(attrs={'class': 'detailmeta r'})[0].findAll('h1')[0].text.strip()
        item_pic = zsoup.findAll(attrs={'class': 'deteilpic l'})[0].findAll('img')[0].attrMap.get('src', '')
        price = zsoup.findAll(attrs={'class': 'nubA clear'})[0].findAll('i')[0].text.strip()

        sproduct.title = title
        sproduct.price = price
        sproduct.pic_url = item_pic
        sproduct.product_link = item_url
        sproduct.sale_supplier = supplier
        sproduct.sale_category = salecategory
        sproduct.save()


    def saveTmallItem(self, tsoup, item_url, category='', **kwargs):

        outer_id = TMALL_ITEM_ID_RE.match(item_url).groupdict().get('item_id')
        sproduct, state = SaleProduct.objects.get_or_create(
            outer_id=outer_id,
            platform=SaleProduct.TMALL)

        bname_tags = tsoup.findAll(attrs={'class': 'slogo-shopname'})
        if not bname_tags:
            return

        brand_name = bname_tags[0].findAll('strong')[0].text.strip()
        salecategory, state = SaleCategory.objects.get_or_create(name=category)

        supplier = self.getOrCreateSupplier(
            supplier_name=brand_name,
            platform=SaleProduct.TMALL,
            category=salecategory)

        title = tsoup.findAll(attrs={'class': 'tb-detail-hd'})[0].findAll('h1')[0].text.strip()
        item_pic = tsoup.findAll(attrs={'class': 'tb-booth'})[0].findAll('img')[0].attrMap.get('src', '')

        sproduct.title = title
        sproduct.price = kwargs.get('item_price', 0)
        sproduct.pic_url = item_pic
        sproduct.product_link = item_url
        sproduct.sale_supplier = supplier
        sproduct.sale_category = salecategory
        sproduct.save()

    def saveTaobaoItem(self, tsoup, item_url, category='', **kwargs):

        outer_id = TMALL_ITEM_ID_RE.match(item_url).groupdict().get('item_id')
        sproduct, state = SaleProduct.objects.get_or_create(
            outer_id=outer_id,
            platform=SaleProduct.TAOBAO)

        bname_tags = tsoup.findAll(attrs={'class': 'tb-seller-name'})
        if not bname_tags:
            return

        brand_name = bname_tags[0].text.strip()
        salecategory, state = SaleCategory.objects.get_or_create(name=category)

        supplier = self.getOrCreateSupplier(
            supplier_name=brand_name,
            platform=SaleProduct.TAOBAO,
            category=salecategory)

        title = tsoup.findAll(attrs={'class': 'tb-main-title'})[0].text.strip()
        item_pic = tsoup.findAll(attrs={'id': 'J_ImgBooth'})[0].attrMap.get('data-src', '')

        sproduct.title = title
        sproduct.price = kwargs.get('item_price', 0)
        sproduct.pic_url = item_pic
        sproduct.product_link = item_url
        sproduct.sale_supplier = supplier
        sproduct.sale_category = salecategory
        sproduct.save()

    def crawItemUrl(self, soup, category=''):

        url_set = set([])
        item_tags = soup.findAll(attrs={'href': self.imatch_re})

        for item_tag in item_tags:
            try:
                item_url = item_tag.attrMap.get('href', '')
                item_uri = item_url.split('?')[0]
                if item_uri in url_set:
                    continue
                url_set.add(item_uri)

                isoup, response = self.getBeaSoupByCrawUrl(item_url)
                resp_url = response.geturl()
                kwargs = {'category': category}

                if resp_url.startswith('http://shop.zhe800.com/products/'):
                    self.saveZ800Item(isoup, resp_url, **kwargs)

                if resp_url.startswith('http://detail.tmall.com/item.htm'):
                    item_price = item_tag.findParent().findAll('h4')[0].findAll('em')[0].text.replace(u'¥', '').replace(
                        '&yen;', '')
                    kwargs.update({'item_price': item_price})
                    self.saveTmallItem(isoup, resp_url, **kwargs)

                if resp_url.startswith('http://item.taobao.com/item.htm'):
                    item_price = item_tag.findParent().findAll('h4')[0].findAll('em')[0].text.replace(u'¥', '').replace(
                        '&yen;', '')
                    kwargs.update({'item_price': item_price})
                    self.saveTaobaoItem(isoup, resp_url, **kwargs)

            except Exception, exc:
                logger.error('ITEM URL ERROR:%s' % exc.message, exc_info=True)

        return len(item_tags)

    def crawItems(self, brand_url, category=''):

        print 'DEBUG BRAND:', datetime.datetime.now(), brand_url
        isoup, response = self.getBeaSoupByCrawUrl(brand_url)
        self.crawItemUrl(isoup, category=category)

    def getPageUrl(self, url, page):

        if url.startswith('http://www.zhe800.com/ju_tag/taofushi'):
            return url + '/page/%s' % page

        if url.startswith('http://www.zhe800.com/ju_type/baoyou'):
            return url + '/page/%s' % page

        if url.startswith('http://www.zhe800.com/zhuanchang/muying'):
            return '%s?%s' % (url, urllib.urlencode({'page': page, 'sort': 'hottest', 'type': 'all'}))
        return url

    def crawBrands(self, url, category=''):

        brand_url_set = set([])
        has_next = True
        page = 1
        while has_next:

            zhe_url = self.getPageUrl(url, page)
            bsoup, response = self.getBeaSoupByCrawUrl(zhe_url)

            brand_tags = bsoup.findAll(
                attrs={'href': re.compile("(^http://brand.zhe800.com/[\w]+|^http://www.zhe800.com/zhuanchang/[\w]+)")})
            for brand_tag in brand_tags:

                brand_url = brand_tag.attrMap.get('href', '')
                if brand_url in brand_url_set:
                    continue

                brand_url_set.add(brand_url)
                self.crawItems(brand_url, category=category)

            item_num = self.crawItemUrl(bsoup, category=category)
            page += 1

            if not item_num:
                has_next = False

    def run(self, *args, **kwargs):

        for craw_url, category_name in self.category_urls:
            self.crawBrands(craw_url, category=category_name)


#############################################################
class CrawXiaoherItemsTask(CrawTask):
    category_urls = (('http://www.xiaoher.com/v2/children', u'母婴'),
                     ('http://www.xiaoher.com/v2/ladys', u'女装'),)

    site_url = 'http://www.xiaoher.com'

    def saveXiaoHerItem(self, tsoup, item_url, category=''):

        outer_id = XHER_ITEM_ID_RE.match(item_url).groupdict().get('item_id')
        sproduct, state = SaleProduct.objects.get_or_create(
            outer_id=outer_id,
            platform=SaleProduct.XIAOHER)
        if sproduct.title:
            return

        bname_tags = tsoup.findAll(attrs={'class': 'brand_name link_underline'})
        if not bname_tags:
            return

        brand_name = bname_tags[0].text.strip().replace(u"品牌：", "")
        salecategory, state = SaleCategory.objects.get_or_create(name=category)

        supplier = self.getOrCreateSupplier(
            supplier_name=brand_name,
            platform=SaleProduct.XIAOHER,
            category=salecategory)

        title = tsoup.findAll(attrs={'class': 'detail_hd clearfix'})[0].findAll(attrs={'class': 'left'})[0].text.strip()
        item_pic = tsoup.findAll(attrs={'class': 'bigPic'})[0].findAll('img')[0].attrMap.get('src', '')
        price = tsoup.findAll(attrs={'class': 'item price  '})[0].findAll('span')[0].text.replace(u'￥', '').replace(
            '&yen;', '')

        psize = tsoup.findAll(attrs={'class': 'item size'})[0]
        hot_value = 0
        if len(psize.findAll(attrs={'class': 's none'})):
            hot_value = 10
            if len(psize.findAll(attrs={'class': 's'})):
                hot_value = 5

        sproduct.title = title
        sproduct.price = price
        sproduct.pic_url = item_pic
        sproduct.product_link = item_url
        sproduct.hot_value = hot_value
        sproduct.sale_supplier = supplier
        sproduct.sale_category = salecategory
        sproduct.platform = SaleProduct.XIAOHER
        sproduct.save()

    def crawItemUrl(self, soup, category=''):

        item_tags = soup.findAll(attrs={'href': re.compile('^/detail/[0-9]+/[0-9]+')})
        for item_tag in item_tags:
            try:
                item_url = '%s%s' % (self.site_url, item_tag.attrMap.get('href', ''))
                isoup, response = self.getBeaSoupByCrawUrl(item_url)
                resp_url = response.geturl()

                self.saveXiaoHerItem(isoup, resp_url, category=category)
            except Exception, exc:
                logger.error('ITEM URL ERROR:%s' % exc.message, exc_info=True)

        return len(item_tags)

    def crawItems(self, brand_url, category=''):

        print 'DEBUG BRAND:', datetime.datetime.now(), brand_url
        isoup, response = self.getBeaSoupByCrawUrl(brand_url)
        self.crawItemUrl(isoup, category=category)

    def getPageUrl(self, url, page):

        return url

    def crawBrands(self, url, category=''):

        brand_url_set = set([])
        has_next = True
        page = 1
        while has_next:

            zhe_url = self.getPageUrl(url, page)
            bsoup, response = self.getBeaSoupByCrawUrl(zhe_url)

            brand_tags = bsoup.findAll(attrs={'href': re.compile("^/show/[0-9]+")})
            for brand_tag in brand_tags:

                brand_url = '%s%s' % (self.site_url, brand_tag.attrMap.get('href', ''))
                if brand_url in brand_url_set:
                    continue

                brand_url_set.add(brand_url)
                self.crawItems(brand_url, category=category)

            item_num = self.crawItemUrl(bsoup, category=category)
            has_next = False

    def run(self, *args, **kwargs):

        for craw_url, category_name in self.category_urls:
            self.crawBrands(craw_url, category=category_name)


#############################################################
class CrawVIPItemsTask(CrawTask):
    category_urls = (('http://category.vip.com/search-2-0-{0}.html?q=1|7830', u'女装'),
                     ('http://category.vip.com/search-2-0-{0}.html?q=1|8053', u'母婴'),)

    site_url = 'http://www.vip.com'

    def saveVIPItem(self, tsoup, item_url, category=''):

        outer_id = VIP_ITEM_ID_RE.match(item_url).groupdict().get('item_id')
        sproduct, state = SaleProduct.objects.get_or_create(
            outer_id=outer_id,
            platform=SaleProduct.VIP)
        if sproduct.title:
            return

        bname_tags = tsoup.findAll(attrs={'class': 'pib-title'})
        if not bname_tags:
            return

        brand_name = bname_tags[0].findAll('a')[0].text.strip()
        salecategory, state = SaleCategory.objects.get_or_create(name=category)

        supplier = self.getOrCreateSupplier(
            supplier_name=brand_name,
            platform=SaleProduct.VIP,
            category=salecategory)

        title = tsoup.findAll(attrs={'class': 'pib-title-detail'})[0].text.strip()
        item_pic = tsoup.findAll(attrs={'class': 'show-midpic '})[0].findAll('img')[0].attrMap.get('src', '')
        price = tsoup.findAll(attrs={'class': 'pi-price-box'})[0].findAll('span')[0].text.replace(u'￥', '').replace(
            '&yen;', '')

        psize = tsoup.findAll(attrs={'class': 'size-list'})[0]
        hot_value = 0
        if len(psize.findAll(attrs={'class': 'size-list-item J-sizeID sli-disabled'})):
            hot_value = 10
            if len(psize.findAll(attrs={'class': 'size-list-item J-sizeID'})):
                hot_value = 5

        sproduct.title = title
        sproduct.price = price
        sproduct.pic_url = item_pic
        sproduct.product_link = item_url
        sproduct.hot_value = hot_value
        sproduct.sale_supplier = supplier
        sproduct.sale_category = salecategory
        sproduct.save()

    def crawItemUrl(self, soup, category=''):

        item_tags = soup.findAll(attrs={'href': re.compile('^http://www.vip.com/detail-[0-9]+-[0-9]+.html')})
        for item_tag in item_tags:
            try:
                item_url = item_tag.attrMap.get('href', '')
                isoup, response = self.getBeaSoupByCrawUrl(item_url)
                resp_url = response.geturl()

                self.saveVIPItem(isoup, resp_url, category=category)
            except Exception, exc:
                logger.error('ITEM URL ERROR:%s' % exc.message, exc_info=True)

        return len(item_tags)

    def crawItems(self, brand_url, category=''):

        print 'DEBUG BRAND:', datetime.datetime.now(), brand_url
        isoup, response = self.getBeaSoupByCrawUrl(brand_url)
        self.crawItemUrl(isoup, category=category)

    def getPageUrl(self, url, page):

        return url.format(page)

    def crawBrands(self, url, category=''):

        has_next = True
        page = 1
        while has_next:

            zhe_url = self.getPageUrl(url, page)
            print 'DEBUG BRAND:', datetime.datetime.now(), zhe_url
            vsoup, response = self.getBeaSoupByCrawUrl(zhe_url)

            item_num = self.crawItemUrl(vsoup, category=category)
            page += 1
            if item_num == 0:
                has_next = False

    def run(self, *args, **kwargs):

        for craw_url, category_name in self.category_urls:
            self.crawBrands(craw_url, category=category_name)

        #############################################################


class CrawJHSItemsTask(CrawTask):
    category_urls = (('http://ju.taobao.com/jusp/nvzhuangpindao/tp.htm?', u'女装'),
                     ('http://ju.taobao.com/jusp/muyingpindao/tp.htm?', u'母婴'),)

    site_url = 'http://detail.tmall.com/item.htm?id={0}'

    def saveJHSItem(self, tsoup, item_url, category='', **kwargs):

        outer_id = TMALL_ITEM_ID_RE.match(item_url).groupdict().get('item_id')
        sproduct, state = SaleProduct.objects.get_or_create(
            outer_id=outer_id,
            platform=SaleProduct.JHS)

        bname_tags = tsoup.findAll(attrs={'class': 'slogo-shopname'})
        if not bname_tags:
            return

        brand_name = bname_tags[0].findAll('strong')[0].text.strip()
        salecategory, state = SaleCategory.objects.get_or_create(name=category)

        supplier = self.getOrCreateSupplier(
            supplier_name=brand_name,
            platform=SaleProduct.JHS,
            category=salecategory)

        title = tsoup.findAll(attrs={'class': 'tb-detail-hd'})[0].findAll('h1')[0].text.strip()[0:64]
        item_pic = tsoup.findAll(attrs={'class': 'tb-booth'})[0].findAll('img')[0].attrMap.get('src', '')

        sproduct.title = title
        sproduct.price = kwargs.get('item_price', 0)
        sproduct.pic_url = item_pic
        sproduct.product_link = item_url
        sproduct.sale_supplier = supplier
        sproduct.sale_category = salecategory
        sproduct.save()

    def crawItemUrl(self, soup, category=''):

        item_tags = soup.findAll(attrs={'href': re.compile('^http://detail.ju.taobao.com/home.htm?')})
        for item_tag in item_tags:
            try:
                tag_url = item_tag.attrMap.get('href', '')
                item_id = JHS_ITEM_ID_RE.match(tag_url).groupdict().get('item_id')
                item_url = self.site_url.format(item_id)

                kwargs = {}
                item_price = item_tag.findAll(attrs={'class': re.compile('J_actPrice|actPrice')})[0].text.replace(u'¥',
                                                                                                                  '').replace(
                    '&yen;', '')
                kwargs.update({'item_price': item_price})

                isoup, response = self.getBeaSoupByCrawUrl(item_url)
                resp_url = response.geturl()

                self.saveJHSItem(isoup, resp_url, category=category, **kwargs)
            except Exception, exc:
                logger.error('ITEM URL ERROR:%s' % exc.message, exc_info=True)

        return len(item_tags)

    def crawItems(self, brand_url, category=''):

        print 'DEBUG BRAND:', datetime.datetime.now(), brand_url
        isoup, response = self.getBeaSoupByCrawUrl(brand_url)
        self.crawItemUrl(isoup, category=category)

    def getPageUrl(self, url, page):

        return url

    def crawBrands(self, url, category=''):

        brand_url_set = set([])
        has_next = True
        page = 1
        while has_next:

            zhe_url = self.getPageUrl(url, page)
            csoup, response = self.getBeaSoupByCrawUrl(zhe_url)

            cat_tags = csoup.findAll(attrs={'data-ajaxurl': re.compile("^http://ju.taobao.com/json/jusp/tpData.htm?")})
            print zhe_url, len(cat_tags)
            for cat_tag in cat_tags:
                ##
                cat_url = cat_tag.attrMap.get('data-ajaxurl', '')
                bsoup, response = self.getBeaSoupByCrawUrl(cat_url)

                brand_tags = bsoup.findAll(attrs={'href': re.compile("^http://ju.taobao.com/tg/brand_items.htm?")})
                for brand_tag in brand_tags:
                    brand_url = brand_tag.attrMap.get('href', '')
                    if brand_url in brand_url_set:
                        continue

                    brand_url_set.add(brand_url)
                    self.crawItems(brand_url, category=category)
                ##
                self.crawItemUrl(bsoup, category=category)
            #
            self.crawItemUrl(csoup, category=category)
            has_next = False

    def run(self, *args, **kwargs):

        for craw_url, category_name in self.category_urls:
            self.crawBrands(craw_url, category=category_name)


        #############################################################


class CrawBBWItemsTask(CrawTask):
    category_urls = (('http://you.beibei.com/', u'母婴'),)

    site_url = 'http://detail.tmall.com/item.htm?id={0}'

    def saveBBWItem(self, tsoup, item_url, category='', **kwargs):

        outer_id = BBW_ITEM_ID_RE.match(item_url).groupdict().get('item_id')
        sproduct, state = SaleProduct.objects.get_or_create(
            outer_id=outer_id,
            platform=SaleProduct.BBW)

        brand_name = self.getBrandName(tsoup)
        if not brand_name:
            return

        salecategory, state = SaleCategory.objects.get_or_create(name=category)

        supplier = self.getOrCreateSupplier(supplier_name=brand_name,
                                            platform=SaleProduct.BBW,
                                            category=salecategory)

        title = tsoup.findAll(attrs={'class': 'title'})[0].findAll('h3')[0].text.strip()[0:64]
        item_pic = tsoup.findAll(attrs={'class': 'view-MainImg'})[0].attrMap.get('src', '')
        item_price = tsoup.findAll(attrs={'class': 'now-price'})[0].text.replace(u'￥', '').replace('&yen;', '')

        sproduct.title = title
        sproduct.price = item_price or 0
        sproduct.pic_url = item_pic
        sproduct.product_link = item_url
        sproduct.sale_supplier = supplier
        sproduct.sale_category = salecategory
        sproduct.save()

    def crawItemUrl(self, soup, category=''):

        item_tags = soup.findAll(attrs={'href': re.compile('^http://you.beibei.com/detail/')})
        for item_tag in item_tags:
            try:
                item_url = item_tag.attrMap.get('href', '')

                isoup, response = self.getBeaSoupByCrawUrl(item_url)
                resp_url = response.geturl()

                self.saveBBWItem(isoup, resp_url, category=category)
            except Exception, exc:
                logger.error('ITEM URL ERROR:%s' % exc.message, exc_info=True)

        return len(item_tags)

    def crawItems(self, brand_url, category=''):

        print 'DEBUG BRAND:', datetime.datetime.now(), brand_url
        isoup, response = self.getBeaSoupByCrawUrl(brand_url)
        self.crawItemUrl(isoup, category=category)

    def getBrandName(self, tsoup):

        bname_tags = tsoup.findAll(attrs={'class': 'props clearfix'})
        if not bname_tags:
            return ""

        for btag in bname_tags[0].findAll('li'):
            label = btag.findAll('b')[0].text.strip()
            if label == u"品牌：":
                return btag.findAll('span')[0].text.strip()
        return ""

    def getPageUrl(self, url, page):

        return url

    def crawBrands(self, url, category=''):

        brand_url_set = set([])
        has_next = True
        page = 1
        while has_next:
            zhe_url = self.getPageUrl(url, page)
            csoup, response = self.getBeaSoupByCrawUrl(zhe_url)

            # cat_tags = csoup.findAll(attrs={'href' : re.compile("^http://www.beibei.com/tuan/detail/")})
            #             for cat_tag in cat_tags:
            #                 ##
            #                 cat_url = cat_tag.attrMap.get('data-ajaxurl','')
            #                 bsoup,response = self.getBeaSoupByCrawUrl(cat_url)
            #
            #                 brand_tags =  bsoup.findAll(attrs={'href' : re.compile("^http://ju.taobao.com/tg/brand_items.htm?")})
            #                 for brand_tag in brand_tags:
            #                     brand_url = brand_tag.attrMap.get('href','')
            #                     if  brand_url in brand_url_set:
            #                         continue
            #
            #                     brand_url_set.add(brand_url)
            #                     self.crawItems(brand_url,category=category)
            #                 ##
            #                 self.crawItemUrl(bsoup, category=category)
            #
            self.crawItemUrl(csoup, category=category)
            has_next = False

    def run(self, *args, **kwargs):

        for craw_url, category_name in self.category_urls:
            self.crawBrands(craw_url, category=category_name)


@task()
def task_calculate_supplier_stats_data(stats_record):
    """
    stats: statistics app SaleStats instance
    """
    supplier_id = stats_record.current_id
    from statistics.models import SaleStats
    from statistics import constants

    supplier = SaleSupplier.objects.filter(id=supplier_id).first()
    if not supplier:
        logger.warn(u'task_calculate_supplier_stats_data stats record %s supplier not found' % stats_record.id)
        return
    statss_res = SaleStats.objects.filter(
        current_id=supplier_id,
        record_type=stats_record.record_type,
        timely_type=stats_record.timely_type).values('status').annotate(s_num=Sum('num'),
                                                                        s_payment=Sum('payment'))  # 同一个供应商　所有的日报
    num_status_map = {
        constants.NOT_PAY: 'no_pay_num',
        constants.PAID: 'pay_num',
        constants.CANCEL: 'cancel_num',
        constants.OUT_STOCK: 'out_stock_num',
        constants.RETURN_GOODS: 'return_good_num',
    }
    amount_status_map = {
        constants.NOT_PAY: '',  # 不写
        constants.PAID: 'payment',
        constants.CANCEL: 'cancel_amount',
        constants.OUT_STOCK: 'out_stock_amount',
        constants.RETURN_GOODS: 'return_good_amount',
    }
    figure = SupplierFigure.objects.filter(supplier_id=supplier.id).first()
    if figure:
        update_fields = []
        for stats_res in statss_res:
            if hasattr(figure, num_status_map[stats_res['status']]):
                if figure.__getattribute__(num_status_map[stats_res['status']]) != stats_res['s_num']:
                    figure.__setattr__(num_status_map[stats_res['status']], stats_res['s_num'])
                    update_fields.append(num_status_map[stats_res['status']])
            if hasattr(figure, amount_status_map[stats_res['status']]):
                if figure.__getattribute__(amount_status_map[stats_res['status']]) != stats_res['s_payment']:
                    figure.__setattr__(amount_status_map[stats_res['status']], stats_res['s_payment'])
                    update_fields.append(amount_status_map[stats_res['status']])
                figure.__setattr__(amount_status_map[stats_res['status']], stats_res['s_payment'])
        # 计算 退货率
        trade_num = figure.return_good_num + figure.pay_num
        return_good_rate = round(float(figure.return_good_num) / trade_num, 4) if trade_num > 0 else 0
        if figure.return_good_rate != return_good_rate:
            figure.return_good_rate = return_good_rate
            update_fields.append('return_good_rate')
        figure.save(update_fields=update_fields)
    else:
        figure = SupplierFigure(supplier=supplier)
        for stats_res in statss_res:
            if hasattr(figure, num_status_map[stats_res['status']]):
                figure.__setattr__(num_status_map[stats_res['status']], stats_res['s_num'])
            if hasattr(figure, amount_status_map[stats_res['status']]):
                figure.__setattr__(amount_status_map[stats_res['status']], stats_res['s_payment'])
        # 计算 退货率
        trade_num = figure.return_good_num + figure.pay_num
        figure.return_good_rate = round(float(figure.return_good_num) / trade_num, 4) if trade_num > 0 else 0
        figure.save()


@task
def task_check_schedule_is_lock():
    """
    检查排期是否锁定
    """
    from common.dingding import DingDingAPI

    now = datetime.datetime.now()
    tomorrow = (now + datetime.timedelta(days=1)).date()
    items = SaleProductManage.objects.filter(sale_time=tomorrow, lock_status=False)

    if not items:
        return

    name = ','.join(set([x.responsible_person_name for x in items]))
    date = tomorrow.strftime('%Y-%m-%d')
    count = items.count()
    msg = u"""%s\n %s日还有%s个排期没有锁定哦。\n\n 点这里进去锁定吧=>http://admin.xiaolumm.com/console/#/schedule\n\n by 小鹿精灵""" % (name, date, count)

    dd = DingDingAPI()
    dd.sendMsg(msg, toparty='4486273')
    dd.sendMsg(msg, touser='0550581811782786')
