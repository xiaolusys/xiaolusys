# -*- coding:utf-8 -*-
import json
import datetime
from django.db import models
from django.db.models import F

from common.utils import update_model_fields
from core.fields import JSONCharMyField
from .base import PayBaseModel

from shopback.items.models import Product, ContrastContent
from .signals import signal_record_supplier_models
from shopback import paramconfig as pcfg

import logging
logger = logging.getLogger(__name__)

class Productdetail(PayBaseModel):
    WASH_INSTRUCTION = '''洗涤时请深色、浅色衣物分开洗涤。最高洗涤温度不要超过40度，不可漂白。有涂层、印花表面不能进行熨烫，会导致表面剥落。不可干洗，悬挂晾干。'''
    OUT_PERCENT = 0  # 未设置代理返利比例
    ZERO_PERCENT = -1
    THREE_PERCENT = 3
    FIVE_PERCENT = 5
    TEN_PERCENT = 10
    TWENTY_PERCENT = 20
    THIRTY_PERCENT = 30

    WEIGHT_CHOICE = ((i, i) for i in range(1, 101)[::-1])
    DISCOUNT_CHOICE = ((i, i) for i in range(1, 101)[::-1])
    BUY_LIMIT_CHOICE = ((i, i) for i in range(1, 21))

    REBETA_CHOICES = ((OUT_PERCENT, u'未设置返利'),
                      (ZERO_PERCENT, u'该商品不返利'),
                      (THREE_PERCENT, u'返利百分之3'),
                      (FIVE_PERCENT, u'返利百分之5'),
                      (TEN_PERCENT, u'返利百分之10'),
                      (TWENTY_PERCENT, u'返利百分之20'),
                      (THIRTY_PERCENT, u'返利百分之30'),)

    product = models.OneToOneField(Product, primary_key=True,
                                   related_name='details', verbose_name=u'库存商品')

    head_imgs = models.TextField(blank=True, verbose_name=u'题头照(多张请换行)')
    content_imgs = models.TextField(blank=True, verbose_name=u'内容照(多张请换行)')

    mama_discount = models.IntegerField(default=100, choices=DISCOUNT_CHOICE, verbose_name=u'妈妈折扣')
    is_recommend = models.BooleanField(db_index=True, default=False, verbose_name=u'专区推荐')
    is_seckill = models.BooleanField(db_index=True, default=False, verbose_name=u'是否秒杀')
    is_sale = models.BooleanField(db_index=True, default=False, verbose_name=u'特价商品')
    order_weight = models.IntegerField(db_index=True, default=8, choices=WEIGHT_CHOICE, verbose_name=u'权值')
    buy_limit = models.BooleanField(db_index=True, default=False, verbose_name=u'是否限购')
    per_limit = models.IntegerField(default=5, choices=BUY_LIMIT_CHOICE, verbose_name=u'限购数量')

    material = models.CharField(max_length=64, blank=True, verbose_name=u'商品材质')
    color = models.CharField(max_length=64, blank=True, verbose_name=u'可选颜色')
    wash_instructions = models.TextField(default=WASH_INSTRUCTION, blank=True, verbose_name=u'洗涤说明')
    note = models.CharField(max_length=256, blank=True, verbose_name=u'备注')
    mama_rebeta = models.IntegerField(default=OUT_PERCENT, choices=REBETA_CHOICES, db_index=True, verbose_name=u'代理返利')

    rebeta_scheme_id = models.IntegerField(default=0, verbose_name=u'返利计划')

    class Meta:
        db_table = 'flashsale_productdetail'
        app_label = 'pay'
        verbose_name = u'特卖商品/详情'
        verbose_name_plural = u'特卖商品/详情列表'

    def __unicode__(self):
        return '<%s,%s>' % (self.product.outer_id, self.product.name)

    def mama_rebeta_rate(self):
        if self.mama_rebeta == self.ZERO_PERCENT:
            return 0.0
        if self.mama_rebeta == self.OUT_PERCENT:
            return None
        rate = self.mama_rebeta / 100.0
        assert rate >= 0 and rate <= 1
        return rate

    def head_images(self):
        return self.head_imgs.split()

    @property
    def content_images(self):
        return self.content_imgs.split()


class ModelProduct(PayBaseModel):
    NORMAL = '0'
    DELETE = '1'
    STATUS_CHOICES = ((NORMAL, u'正常'),
                      (DELETE, u'作废'))

    # UP_SHELF = 1
    # DOWN_SHELF = 0

    # SHELF_CHOICES = ((UP_SHELF,u'已上架'),
    #                 (DOWN_SHELF,u'未上架'))

    name = models.CharField(max_length=64, db_index=True, verbose_name=u'款式名称')

    head_imgs = models.TextField(blank=True, verbose_name=u'题头照(多张请换行)')

    content_imgs = models.TextField(blank=True, verbose_name=u'内容照(多张请换行)')

    buy_limit = models.BooleanField(default=False, verbose_name=u'是否限购')
    per_limit = models.IntegerField(default=5, verbose_name=u'限购数量')

    sale_time = models.DateField(null=True, blank=True, db_index=True, verbose_name=u'上架日期')

    # category_id = models.IntegerField(default=0, db_index=True, verbose_name=u'分类ID')
    # lowest_agent_price = models.IntegerField(default=5, verbose_name=u'最低出售价')
    # lowest_std_sale_price = models.IntegerField(default=5, verbose_name=u'最低吊牌价')

    status = models.CharField(max_length=16, db_index=True,
                              choices=STATUS_CHOICES,
                              default=NORMAL, verbose_name=u'状态')

    class Meta:
        db_table = 'flashsale_modelproduct'
        unique_together = ("id", "name")
        app_label = 'pay'
        verbose_name = u'特卖商品/款式'
        verbose_name_plural = u'特卖商品/款式列表'
        permissions = [
            ("change_name_permission", u"修改名字"),
        ]

    def __unicode__(self):
        return '<%s,%s>' % (self.id, self.name)

    def head_img(self):
        return self.head_imgs and self.head_imgs.split()[0] or ''

    head_img_url = property(head_img)

    @property
    def content_images(self):
        return self.content_imgs.split()

    @property
    def head_images(self):
        head_imgs = []
        for product in self.products:
            head_imgs.append(product.PIC_PATH)
        return head_imgs

    @property
    def is_single_spec(self):
        """ 是否单颜色 """
        if self.id <= 0:
            return True
        products = Product.objects.filter(model_id=self.id, status=Product.NORMAL)
        if products.count() > 1:
            return False
        return True

    @property
    def item_product(self):
        if not hasattr(self, '__first_product__'):
            product = self.products.first()
            if not product or not product.detail:
                return None
            self.__first_product__ = product
        return self.__first_product__

    @property
    def is_sale_out(self):
        """ 是否卖光 """
        all_sale_out = True
        for product in self.products:
            all_sale_out &= product.is_sale_out()
        return all_sale_out

    @property
    def model_code(self):
        product = self.item_product
        if not product:
            return ''
        return product.outer_id[0:-1]

    @property
    def is_recommend(self):
        """ 是否推荐 """
        product = self.item_product
        if not product or not product.detail:
            return False
        return product.detail.is_recommend

    @property
    def sale_time(self):
        """  上架时间 """
        product = self.item_product
        if not product or not product.detail:
            return False
        return product.sale_time

    @property
    def category(self):
        """  上架时间 """
        product = self.item_product
        if not product or not product.category:
            return {}
        return {'id': product.category_id}

    @property
    def offshelf_time(self):
        """ 下架时间 """
        product = self.item_product
        if not product or not product.detail:
            return False
        return product.offshelf_time

    @property
    def is_saleopen(self):
        """ 是否新售 """
        product = self.item_product
        if not product or not product.detail:
            return False
        return product.sale_open()

    @property
    def is_newsales(self):
        """ 是否新售 """
        product = self.item_product
        if not product or not product.detail:
            return False
        return product.new_good()

    @property
    def lowest_agent_price(self):
        """ 最低售价 """
        lowest_price = 0
        for product in self.products:
            if lowest_price == 0:
                lowest_price = product.lowest_price()
            else:
                lowest_price = min(lowest_price, product.lowest_price())
        return lowest_price

    @property
    def lowest_std_sale_price(self):
        """ 最低吊牌价 """
        product = self.item_product
        return product and product.std_sale_price or 0

    @property
    def properties(self):
        """ 商品属性 """
        product = self.item_product
        if not product:
            return {}
        detail = product.detail
        return {
            "material": detail.material,
            "wash_instructions": detail.wash_instructions,
            "note": detail.note,
            "color": detail.color
        }

    @property
    def products(self):
        return Product.objects.filter(model_id=self.id, status=pcfg.NORMAL)

    def product_simplejson(self, product):
        sku_list = []
        for sku in product.normal_skus:
            sku_list.append({
                'type':'size',
                'sku_id':sku.id,
                'name':sku.name,
                'free_num':sku.free_num,
                'is_saleout':self.is_sale_out,
                'std_sale_price':sku.std_sale_price,
                'agent_price':sku.agent_price,
            })
        return {
            'type':'color',
            'product_id':product.id,
            'name':product.property_name,
            'product_img': product.pic_path,
            'outer_id': product.outer_id,
            'std_sale_price':product.std_sale_price,
            'agent_price':product.agent_price,
            'lowest_price': product.lowest_price(),
            'sku_items': sku_list
        }

    @property
    def detail_content(self):
        return {
            'name': self.name,
            'model_code': self.model_code,
            'head_imgs': self.head_images,
            'content_imgs': self.content_images,
            'is_single_spec': self.is_single_spec,
            'is_sale_out': self.is_sale_out,
            'is_recommend':self.is_recommend,
            'is_saleopen': self.is_saleopen,
            'is_newsales': self.is_newsales,
            'lowest_agent_price': self.lowest_agent_price,
            'lowest_std_sale_price': self.lowest_std_sale_price,
            'category': self.category,
            'sale_time': self.sale_time,
            'offshelf_time': self.offshelf_time,
            'properties':self.properties,
            'watermark_op': '',
            'item_marks': ['包邮'],
        }

    @property
    def sku_info(self):
        product_list = []
        products = self.products
        for p in products:
            product_list.append(self.product_simplejson(p))

        return product_list

    def format_contrast2table(self, origin_contrast):
        result_data = []
        constants_maps = ContrastContent.contrast_maps()
        constant_set  = set()
        for k1, v1 in origin_contrast.items():
            constant_set.update(v1)

        constant_keys = list(constant_set)
        result_data.append([u'尺码'])
        for k in constant_keys:
            result_data[0].append(constants_maps.get(k, k))

        for k1, v1 in origin_contrast.items():
            temp_list = []
            for key in constant_keys:
                val = v1.get(key, '-')
                temp_list.append(val)
            result_data.append([k1] + temp_list)
        return result_data

    @property
    def comparison(self):
        p_tables = []
        uni_set  = set()
        try:
            for p in self.products:
                contrast_origin = p.contrast.contrast_detail
                uni_key = ''.join(sorted(contrast_origin.keys()))
                if uni_key not in uni_set:
                    uni_set.add(uni_key)
                    p_tables.append({'table':self.format_contrast2table(contrast_origin)})
        except Exception, exc:
            logger.error(exc.message,exc_info=True)
        return {
            'tables': p_tables,
            'metrics': {
                'table':[
                    [u'厚度指数', u'偏薄', u'适中',u'偏厚',u'加厚' ],
                    [u'弹性指数', u'无弹性', u'微弹性',u'适中', u'强弹性'],
                    [u'触感指数', u'偏硬', u'柔软', u'适中', u'超柔'],
                ],
                'choices':[2,3,2]
            },
        }

    @property
    def extras(self):
        return {
            'is_product_buy_limit': True,
            'per_limit_buy_num': 3,
        }


def create_Model_Product(sender, obj, **kwargs):
    pro = obj.item_product
    if isinstance(pro, Product):
        sal_p, supplier = pro.pro_sale_supplier()
        if supplier is not None:
            supplier.total_select_num = F('total_select_num') + 1
            update_model_fields(supplier, update_fields=['total_select_num'])


signal_record_supplier_models.connect(create_Model_Product, sender=ModelProduct)

DEFAULT_WEN_POSTER = [
    {
        "subject": ['2折起', '小鹿美美  女装专场'],
        "item_link": "/mall/#/product/list/lady",
        "app_link": "com.jimei.xlmm://app/v1/products/ladylist",
        "pic_link": ""
    }
]

DEFAULT_CHD_POSTER = [
    {
        "subject": ['2折起', '小鹿美美  童装专场'],
        "item_link": "/mall/#/product/list/child",
        "app_link": "com.jimei.xlmm://app/v1/products/childlist",
        "pic_link": ""
    }
]

def default_wen_poster():
    return json.dumps(DEFAULT_WEN_POSTER, indent=2)

def default_chd_poster():
    return json.dumps(DEFAULT_WEN_POSTER, indent=2)

class GoodShelf(PayBaseModel):
    DEFAULT_WEN_POSTER = DEFAULT_WEN_POSTER
    DEFAULT_CHD_POSTER = DEFAULT_CHD_POSTER

    title = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'海报名称')

    wem_posters = JSONCharMyField(max_length=10240, blank=True,
                                  default=default_wen_poster,
                                  verbose_name=u'女装海报')
    chd_posters = JSONCharMyField(max_length=10240, blank=True,
                                  default=default_chd_poster,
                                  verbose_name=u'童装海报')

    is_active = models.BooleanField(default=True, verbose_name=u'上线')
    active_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'上线日期')

    class Meta:
        db_table = 'flashsale_goodshelf'
        app_label = 'pay'
        verbose_name = u'特卖商品/海报'
        verbose_name_plural = u'特卖商品/海报列表'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.title)

    def get_cat_imgs(self):
        return [
            {'id': 5, 'name': u'童装专区',
             'cat_img': 'http://7xogkj.com2.z0.glb.qiniucdn.com/category/child.png',
             'cat_link': '/mall/#/product/list/child'},
            {'id': 8, 'name': u'女装专区',
             'cat_img': 'http://7xogkj.com2.z0.glb.qiniucdn.com/category/lady.png',
             'cat_link': '/mall/#/product/list/lady'},
        ]

    def get_posters(self):
        return self.wem_posters + self.chd_posters

    def get_activity(self):
        return ActivityEntry.get_default_activity()

    def get_current_activitys(self):
        now = datetime.datetime.now()
        return ActivityEntry.get_landing_effect_activitys(now)

    def get_brands(self):
        return BrandEntry.get_brand()


class ActivityEntry(PayBaseModel):
    """ 商城活动入口 """

    ACT_COUPON = 'coupon'
    ACT_WEBVIEW = 'webview'
    ACT_MAMA = 'mama'

    ACT_CHOICES = (
        (ACT_COUPON, u'优惠券活动'),
        (ACT_WEBVIEW, u'商城活动页'),
        (ACT_MAMA, u'妈妈活动'),
    )

    title = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'活动名称')

    act_desc = models.TextField(max_length=512, blank=True, verbose_name=u'活动描述')
    act_img = models.CharField(max_length=256, blank=True, verbose_name=u'活动入口图片')
    act_link = models.CharField(max_length=256, blank=True, verbose_name=u'活动链接')
    mask_link = models.CharField(max_length=256, blank=True, verbose_name=u'活动弹窗提示图')
    act_applink = models.CharField(max_length=256, blank=True, verbose_name=u'活动APP协议链接')
    share_icon = models.CharField(max_length=128, blank=True, verbose_name=u'活动分享图片')
    share_link = models.CharField(max_length=256, blank=True, verbose_name=u'活动分享链接')
    act_type = models.CharField(max_length=8, choices=ACT_CHOICES,
                                db_index=True, verbose_name=u'活动类型')

    login_required = models.BooleanField(default=False, verbose_name=u'需要登陆')
    start_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'开始时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name=u'结束时间')

    order_val = models.IntegerField(default=0, verbose_name=u'排序值')

    extras = JSONCharMyField(max_length=5120, default={}, blank=True, verbose_name=u'活动数据')
    is_active = models.BooleanField(default=True, verbose_name=u'上线')

    class Meta:
        db_table = 'flashsale_activity_entry'
        app_label = 'pay'
        verbose_name = u'特卖/商城活动入口'
        verbose_name_plural = u'特卖/商城活动入口'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.title)

    @classmethod
    def get_default_activity(cls):
        acts = cls.objects.filter(is_active=True,
                                  end_time__gte=datetime.datetime.now()) \
            .exclude(act_type=ActivityEntry.ACT_MAMA).order_by('-order_val', '-modified')
        if acts.exists():
            return acts[0]
        return None

    @classmethod
    def get_effect_activitys(cls, active_time):
        """ 根据时间获取活动列表 """
        acts = cls.objects.filter(is_active=True,
                                  end_time__gte=active_time) \
            .order_by('-order_val', '-modified')
        if acts.exists():
            return acts
        return cls.objects.none()

    @classmethod
    def get_landing_effect_activitys(cls, active_time):
        """ 根据时间获取活动列表app首页展示 """
        acts = cls.objects.filter(is_active=True,
                                  end_time__gte=active_time) \
            .exclude(act_type=ActivityEntry.ACT_MAMA).order_by('-order_val', '-modified')
        if acts.exists():
            return acts
        return cls.objects.none()

    def get_shareparams(self, **params):
        return {
            'id': self.id,
            'title': self.title.format(**params),
            'share_type': 'link',
            'share_icon': self.share_icon,
            'share_link': self.share_link.format(**params),
            'active_dec': self.act_desc.format(**params),
        }

    def get_html(self, key):
        htmls = self.extras["html"]
        if key in htmls:
            return htmls[key]
        return None

    def total_member_num(self):
        return 2000

    def friend_member_num(self):
        return 16


class BrandEntry(PayBaseModel):
    """ 品牌推广入口 """

    id = models.AutoField(primary_key=True)
    brand_name = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'品牌名称')

    brand_desc = models.TextField(max_length=512, blank=True, verbose_name=u'品牌活动描述')
    brand_pic = models.CharField(max_length=256, blank=True, verbose_name=u'品牌图片')
    brand_post = models.CharField(max_length=256, blank=True, verbose_name=u'品牌海报')
    brand_applink = models.CharField(max_length=256, blank=True, verbose_name=u'品牌APP协议链接')

    start_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'开始时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name=u'结束时间')

    order_val = models.IntegerField(default=0, verbose_name=u'排序值')
    is_active = models.BooleanField(default=True, verbose_name=u'上线')

    class Meta:
        db_table = 'flashsale_brand_entry'
        app_label = 'pay'
        verbose_name = u'特卖/品牌推广入口'
        verbose_name_plural = u'特卖/品牌推广入口'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.brand_name)

    @classmethod
    def get_brand(cls):
        acts = cls.objects.filter(is_active=True)
        if acts.exists():
            return acts
        return []

    @classmethod
    def get_effect_brands(cls, btime):
        """ 根据时间获取活动列表 """
        brands = cls.objects.filter(is_active=True,
                                    end_time__gte=btime) \
            .order_by('-order_val', '-modified')
        if brands.exists():
            return brands
        return cls.objects.none()


class BrandProduct(PayBaseModel):
    """ 品牌商品信息 """

    id = models.AutoField(primary_key=True)
    brand = models.ForeignKey(BrandEntry, related_name='brand_products', verbose_name=u'品牌编号id')
    brand_name = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'品牌名称')

    product_id = models.BigIntegerField(db_index=True, default=0, verbose_name=u'商品id')
    product_name = models.CharField(max_length=64, blank=True, verbose_name=u'商品名称')
    product_img = models.CharField(max_length=256, blank=True, verbose_name=u'商品图片')

    start_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'开始时间')
    end_time = models.DateTimeField(blank=True, null=True, verbose_name=u'结束时间')

    class Meta:
        db_table = 'flashsale_brand_product'
        app_label = 'pay'
        verbose_name = u'特卖/品牌商品'
        verbose_name_plural = u'特卖/品牌商品'

    def __unicode__(self):
        return u'<%s,%s>' % (self.id, self.brand_name)

    def save(self, *args, **kwargs):
        if not self.brand_name:
            self.brand_name = self.brand.brand_name
        if not self.product_name:
            self.product_name = self.prodouct.name
            self.product_img = self.prodouct.head_img()
        return super(BrandProduct, self).save(*args, **kwargs)

    @property
    def prodouct(self):
        if not hasattr(self, '_product_'):
            self._product_ = Product.objects.get(id=self.product_id)
        return self._product_

    def product_lowest_price(self):
        """ 商品最低价 """
        return self.prodouct.product_lowest_price()

    def product_std_sale_price(self):
        """ 商品吊牌价 """
        return self.prodouct.std_sale_price
