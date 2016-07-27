# -*- coding:utf-8 -*-
import json
import datetime
from django.db import models
from django.db.models import F

from tagging.fields import TagField
from common.utils import update_model_fields
from core.fields import JSONCharMyField
from core.models import BaseTagModel
from .base import PayBaseModel, BaseModel

from shopback.items.models import Product, ProductSkuContrast, ContrastContent
from ..signals import signal_record_supplier_models
from shopback import paramconfig as pcfg
from shopback.items.constants import SKU_CONSTANTS_SORT_MAP as SM, PROPERTY_NAMES

import logging
logger = logging.getLogger(__name__)

WASH_INSTRUCTION ='''洗涤时请深色、浅色衣物分开洗涤。最高洗涤温度不要超过40度，不可漂白。
有涂层、印花表面不能进行熨烫，会导致表面剥落。不可干洗，悬挂晾干。'''.replace('\n','')

class Productdetail(PayBaseModel):
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

    product = models.OneToOneField(Product, primary_key=True, auto_created=True,
                                   related_name='details', verbose_name=u'库存商品')

    head_imgs = models.TextField(blank=True, verbose_name=u'题头照(多张请换行)')
    content_imgs = models.TextField(blank=True, verbose_name=u'内容照(多张请换行)')

    mama_discount = models.IntegerField(default=100, choices=DISCOUNT_CHOICE, verbose_name=u'妈妈折扣')
    is_seckill = models.BooleanField(db_index=True, default=False, verbose_name=u'秒杀')

    is_recommend = models.BooleanField(db_index=True, default=False, verbose_name=u'专区推荐')
    is_sale = models.BooleanField(db_index=True, default=False, verbose_name=u'专场')
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

    def update_order_weight(self, order_weight):
        if self.order_weight != order_weight:
            self.order_weight = order_weight
            self.save(update_fields=['order_weight'])
            return True
        return False

def default_modelproduct_extras_tpl():
    return {
        "saleinfos": {
            "is_product_buy_limit": True,
            "per_limit_buy_num": 3,
        },
        "properties": {},
    }

class ModelProduct(BaseTagModel):

    NORMAL = '0'
    DELETE = '1'
    STATUS_CHOICES = (
        (NORMAL, u'正常'),
        (DELETE, u'作废')
    )
    # UP_SHELF = 1
    # DOWN_SHELF = 0

    # SHELF_CHOICES = ((UP_SHELF,u'已上架'),
    #                 (DOWN_SHELF,u'未上架'))

    name = models.CharField(max_length=64, db_index=True, verbose_name=u'款式名称')

    head_imgs = models.TextField(blank=True, verbose_name=u'题头照(多张请换行)')
    content_imgs = models.TextField(blank=True, verbose_name=u'内容照(多张请换行)')

    salecategory = models.ForeignKey('supplier.SaleCategory', null=True, default=None,
                                     related_name='model_product_set', verbose_name=u'分类')
    # lowest_agent_price = models.IntegerField(default=5, verbose_name=u'最低出售价')
    # lowest_std_sale_price = models.IntegerField(default=5, verbose_name=u'最低吊牌价')

    is_flatten = models.BooleanField(default=False, db_index=True, verbose_name=u'平铺显示')
    extras  = JSONCharMyField(max_length=5000, default=default_modelproduct_extras_tpl, verbose_name=u'附加信息')
    status = models.CharField(max_length=16, db_index=True,
                              choices=STATUS_CHOICES,
                              default=NORMAL, verbose_name=u'状态')

    class Meta:
        db_table = 'flashsale_modelproduct'
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
            if not product:
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
            return None
        return product.sale_time

    @property
    def category(self):
        """  分类 """
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
        if not product or not product.detail:
            return {}
        detail = product.detail
        return {
            "material": detail.material,
            "wash_instructions": detail.wash_instructions,
            "note": detail.note,
            "color": detail.color
        }

    @property
    def attributes(self):
        product = self.item_product
        if not product:
            return {}
        detail = product.detail
        prop_value_list = [('model_code', self.model_code)]
        if detail:
            for key in ('material', 'color', 'wash_instructions', 'note'):
                prop_value_list.append((key, getattr(detail, key)))
        for item in self.extras.get('properties', {}).iteritems():
            prop_value_list.append(item)
        return [{'name': PROPERTY_NAMES.get(prop[0]), 'value':prop[1]} for prop in prop_value_list if prop[1].strip()]

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
            'is_sale_out': self.is_sale_out,
            'is_recommend':self.is_recommend,
            'is_saleopen': self.is_saleopen,
            'is_flatten': self.is_flatten,
            'is_newsales': self.is_newsales,
            'lowest_agent_price': self.lowest_agent_price,
            'lowest_std_sale_price': self.lowest_std_sale_price,
            'category': self.category,
            'sale_time': self.sale_time,
            'offshelf_time': self.offshelf_time,
            'properties':self.properties,
            'watermark_op': '',
            'item_marks': [u'包邮'],
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
        tmp_result = []
        for k1, v1 in origin_contrast.items():
            temp_list = []
            for key in constant_keys:
                val = v1.get(key, '-')
                temp_list.append(val)
            tmp_result.append([k1] + temp_list)
        tmp_result.sort(key=lambda x:SM.find(x[0][0:2]) if SM.find(x[0][0:2])>-1 else SM.find(x[0][0:1]))
        return result_data + tmp_result

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
        except ProductSkuContrast.DoesNotExist:
            logger.warn('ProductSkuContrast not exists:%s'%(p.outer_id))
        except Exception, exc:
            logger.error(exc.message,exc_info=True)
        return {
            'attributes': self.attributes,
            'tables': p_tables,
            'metrics': {
                # 'table':[
                #     [u'厚度指数', u'偏薄', u'适中',u'偏厚',u'加厚' ],
                #     [u'弹性指数', u'无弹性', u'微弹性',u'适中', u'强弹性'],
                #     [u'触感指数', u'偏硬', u'柔软', u'适中', u'超柔'],
                # ],
                # 'choices':[2,3,2]
            },
        }


def create_Model_Product(sender, obj, **kwargs):
    pro = obj.item_product
    if isinstance(pro, Product):
        sal_p, supplier = pro.pro_sale_supplier()
        if supplier is not None:
            supplier.total_select_num = F('total_select_num') + 1
            update_model_fields(supplier, update_fields=['total_select_num'])


signal_record_supplier_models.connect(create_Model_Product, sender=ModelProduct)
