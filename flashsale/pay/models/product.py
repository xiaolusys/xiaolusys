# coding=utf-8
from __future__ import unicode_literals

import re
import json
import datetime
import urlparse
from django.db import models
from django.db.models import F
from django.conf import settings
from django.db.models.signals import post_save
from django.core.cache import cache

from common.utils import update_model_fields
from core.fields import JSONCharMyField
from core.models import BaseTagModel
from core.options import get_systemoa_user, log_action, CHANGE

from shopback import paramconfig as pcfg
from shopback.items.models import Product, ProductSku, ProductSkuContrast, ContrastContent
from shopback.items.constants import SKU_CONSTANTS_SORT_MAP as SM, PROPERTY_NAMES, PROPERTY_KEYMAP
from shopback.items.tasks_stats import task_product_upshelf_notify_favorited_customer
from .base import PayBaseModel, BaseModel
from ..signals import signal_record_supplier_models
from ..managers import modelproduct

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

    product = models.OneToOneField(Product, primary_key=True,
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

    def update_weight_and_recommend(self, is_topic, order_weight, is_recommend):
        p_detail_update_fields = []
        if self.is_sale != is_topic:
            self.is_sale = is_topic
            p_detail_update_fields.append('is_sale')
        if self.order_weight != order_weight:
            self.order_weight = order_weight
            p_detail_update_fields.append('order_weight')
        if self.is_recommend != is_recommend:
            self.is_recommend = is_recommend
            p_detail_update_fields.append('is_recommend')
        if p_detail_update_fields:
            self.save(update_fields=p_detail_update_fields)
            return True


def default_modelproduct_extras_tpl():
    return {
        "saleinfos": {
            "is_product_buy_limit": True,
            "per_limit_buy_num": 20,
        },
        "properties": {},
    }


class ModelProduct(BaseTagModel):

    API_CACHE_KEY_TPL = 'api_modelproduct_{0}'

    NORMAL = 'normal'
    DELETE = 'delete'
    STATUS_CHOICES = (
        (NORMAL, u'正常'),
        (DELETE, u'作废')
    )

    ON_SHELF = 'on'
    OFF_SHELF = 'off'
    WILL_SHELF = 'will'  # 即将上新
    SHELF_CHOICES = (
        (ON_SHELF, u'已上架'),
        (OFF_SHELF, u'未上架')
    )

    USUAL_TYPE    = 0
    VIRTUAL_TYPE  = 1
    NOT_SALE_TYPE = 2
    TYPE_CHOICES = (
        (USUAL_TYPE, u'商品'),
        (VIRTUAL_TYPE, u'虚拟商品'),
        (NOT_SALE_TYPE, u'非卖品'),
    )

    name = models.CharField(max_length=64, db_index=True, verbose_name=u'款式名称')

    head_imgs = models.TextField(blank=True, verbose_name=u'题头照(多张请换行)')
    content_imgs = models.TextField(blank=True, verbose_name=u'内容照(多张请换行)')

    salecategory = models.ForeignKey('supplier.SaleCategory', null=True, default=None,
                                     related_name='modelproduct_set', verbose_name=u'分类')

    lowest_agent_price = models.FloatField(default=0.0, db_index=True, verbose_name=u'最低售价')
    lowest_std_sale_price = models.FloatField(default=0.0, verbose_name=u'最低原价')

    is_onsale    = models.BooleanField(default=False, db_index=True, verbose_name=u'特价/秒杀')
    is_teambuy   = models.BooleanField(default=False, db_index=True, verbose_name=u'团购')
    is_recommend = models.BooleanField(default=False, db_index=True, verbose_name=u'推荐商品')
    is_topic     = models.BooleanField(default=False, db_index=True, verbose_name=u'专题商品')
    is_flatten   = models.BooleanField(default=False, db_index=True, verbose_name=u'平铺显示')
    is_watermark = models.BooleanField(default=False, db_index=True, verbose_name=u'图片水印')
    is_boutique  = models.BooleanField(default=False, db_index=True, verbose_name=u'精品汇')

    teambuy_price = models.FloatField(default=0, verbose_name=u'团购价')
    teambuy_person_num = models.IntegerField(default=3, verbose_name=u'团购人数')

    shelf_status = models.CharField(max_length=8, choices=SHELF_CHOICES,
                                    default=OFF_SHELF, db_index=True, verbose_name=u'上架状态')
    onshelf_time  = models.DateTimeField(default=None, blank=True, db_index=True, null=True, verbose_name=u'上架时间')
    offshelf_time = models.DateTimeField(default=None, blank=True, db_index=True, null=True, verbose_name=u'下架时间')

    order_weight = models.IntegerField(db_index=True, default=50, verbose_name=u'权值')
    rebeta_scheme_id = models.IntegerField(default=0, verbose_name=u'返利计划ID')
    saleproduct  = models.ForeignKey('supplier.SaleProduct', null=True, default=None,
                                     related_name='modelproduct_set', verbose_name=u'特卖选品')

    extras  = JSONCharMyField(max_length=5000, default=default_modelproduct_extras_tpl, verbose_name=u'附加信息')
    status = models.CharField(max_length=16, db_index=True, choices=STATUS_CHOICES,
                              default=NORMAL, verbose_name=u'状态')
    product_type = models.IntegerField(choices=TYPE_CHOICES, default=0, db_index=True, verbose_name=u'商品类型')
    objects = modelproduct.ModelProductManager()

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

    def delete(self, using=None):
        self.status = self.DELETE
        self.save()

    def head_img(self):
        return self.head_imgs and self.head_imgs.split()[0] or ''

    head_img_url = property(head_img)

    @property
    def content_images(self):
        return self.content_imgs.split()

    @property
    def head_images(self):
        # head_imgs = []
        # for product in self.productobj_list:
        #     head_imgs.append(product.PIC_PATH)
        return list(self.products.values_list('pic_path', flat=True))

    @property
    def is_single_spec(self):
        """ 是否单颜色 """
        if self.id <= 0:
            return True
        if len(self.productobj_list) > 1:
            return False
        return True

    @property
    def item_product(self):
        if not hasattr(self, '__first_product__'):
            products = self.productobj_list
            if not products:
                return None
            self.__first_product__ = products[0]
        return self.__first_product__

    @property
    def is_sale_out(self):
        """ 是否卖光 """
        if not hasattr(self, '_is_saleout_'):
            all_sale_out = True
            for product in self.productobj_list:
                all_sale_out &= product.is_sale_out()
            self._is_saleout_ = all_sale_out
        return self._is_saleout_

    @property
    def is_boutique_product(self):
        return int(self.product_type) == ModelProduct.USUAL_TYPE and self.is_boutique

    @property
    def is_boutique_coupon(self):
        return int(self.product_type) == ModelProduct.VIRTUAL_TYPE and self.is_boutique

    def get_web_url(self):
        return urlparse.urljoin(settings.M_SITE_URL, Product.MALL_PRODUCT_TEMPLATE_URL.format(self.id))

    @property
    def model_code(self):
        product = self.item_product
        if not product:
            return ''
        return product.outer_id[0:-1]

    @property
    def sale_time(self):
        """  上架时间 """
        product = self.item_product
        if not product or not product.detail:
            return None
        return product.sale_time

    @property
    def sale_state(self):
        if self.shelf_status == self.OFF_SHELF and \
                (not self.onshelf_time or self.onshelf_time > datetime.datetime.now()):
            return self.WILL_SHELF
        return self.shelf_status

    @property
    def category(self):
        """  分类 """
        product = self.item_product
        if not product or not product.category:
            return {}
        return {'id': product.category_id}

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
    def properties(self):
        """ 商品属性 """
        return {}

    @property
    def attributes(self):
        new_properties = self.extras.get('new_properties')
        if new_properties :
            new_properties.insert(0,{'name': u'商品编码', 'value':self.model_code})
            for props in new_properties:
                props['value'] = re.sub('^\[.*\]','', props['value'])
            return new_properties

        product = self.item_product
        if not product:
            return []
        detail = product.detail
        prop_value_dict = {'model_code': self.model_code}
        model_properties = self.extras.get('properties', {})
        prop_value_dict.update(model_properties)

        if not model_properties and detail:
            for key in ('material', 'color', 'wash_instructions', 'note'):
                prop_value_dict[key] = getattr(detail, key)

        if isinstance(model_properties, dict):
            attrs = sorted(prop_value_dict.items(), key=lambda x: PROPERTY_KEYMAP.get(x[0], 100))
            PROPERTY_NAME_DICT = dict(PROPERTY_NAMES)
            attr_dict = [{'name': PROPERTY_NAME_DICT.get(key), 'value': value} for key, value in attrs
                         if value.strip() and PROPERTY_NAME_DICT.get(key)]
            return attr_dict
        if isinstance(model_properties, list):
            return model_properties
        return []

    @property
    def products(self):
        return Product.objects.filter(model_id=self.id, status=pcfg.NORMAL)

    @property
    def productobj_list(self):
        if not hasattr(self, '_productobj_list_'):
            self._productobj_list_ = list(self.products)
        return self._productobj_list_

    def product_simplejson(self, product):
        sku_list = []
        skuobj_list = product.normal_skus
        for sku in skuobj_list:
            sku_list.append({
                'type':'size',
                'sku_id':sku.id,
                'name':sku.name,
                'free_num':sku.free_num,
                'is_saleout': sku.free_num <= 0,
                'std_sale_price':sku.std_sale_price,
                'agent_price':sku.agent_price,
            })
        return {
            'type':'color',
            'product_id':product.id,
            'name':product.property_name,
            'product_img': product.pic_path,
            'outer_id': product.outer_id,
            'is_saleout': product.is_sale_out(),
            'std_sale_price':product.std_sale_price,
            'agent_price':product.agent_price,
            'lowest_price': product.lowest_price(),
            'sku_items': sku_list,
            'elite_score': product.elite_score
        }

    @property
    def detail_content(self):
        head_imgs = [i for i in self.head_imgs.split() if i.strip()]
        return {
            'name': self.name,
            'model_code': self.model_code,
            'head_img': len(head_imgs) > 0 and head_imgs[0] or '',
            'head_imgs': self.head_images,
            'content_imgs': self.content_images,
            'is_sale_out': False, #self.is_sale_out,
            'is_onsale': self.is_onsale,
            'is_boutique': self.is_boutique,
            'is_recommend':self.is_recommend,
            'is_saleopen': self.is_saleopen,
            'is_flatten': self.is_flatten,
            'is_newsales': self.is_newsales,
            'product_type': self.product_type,
            'lowest_agent_price': self.lowest_agent_price,
            'lowest_std_sale_price': self.lowest_std_sale_price,
            'category': {'id': self.salecategory_id},
            'sale_time': self.onshelf_time,
            'onshelf_time': self.onshelf_time,
            'offshelf_time': self.offshelf_time,
            'sale_state': self.sale_state,
            'properties':self.properties,
            'watermark_op': '',
            'item_marks': [u'包邮'],
            'web_url': self.get_web_url()
        }

    @property
    def sku_info(self):
        product_list = []
        for p in self.productobj_list:
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

    def reset_new_propeties_table_by_comparison(self):
        """
        功能：　设置　extras　的　new_properties 键　的尺码表内容　从　以前的尺码表中读取数据来填充
        """
        old_table = self.comparison['tables']
        if not old_table:
            return
        tt = old_table[0]
        table = tt['table']
        t_head = table[0]
        t_bodys = table[1::]
        values = []
        for t_body in t_bodys:
            c = 0
            dic = {}
            for x in t_body:
                dic.update({t_head[c]: x})
                c += 1
            values.append(dic)
        current_new_properties = self.extras.get('new_properties') or None
        table_head = {"name": "尺码对照参数", "value": t_head}
        table_body = {"name": "尺码表", "value": values}
        if not current_new_properties:
            new_properties = [table_head, table_body]
        else:
            for x in current_new_properties:
                if x.get('name') == '尺码对照参数':
                    x['value'] = t_head
                if x.get('name') == '尺码表':
                    x['value'] = values
            new_properties = current_new_properties
        self.extras.update({'new_properties': new_properties})
        self.save(update_fields=['extras'])
        return

    def set_tables_into_extras(self):
        """
        功能: 将　self.comparison　中 的尺码表保存到extras 中
        """
        old_tables = self.comparison['tables']
        if not old_tables:
            return
        self.extras.update({'tables': old_tables})
        self.save(update_fields=['extras'])
        return

    @property
    def comparison(self):
        uni_set = set()
        constrast_detail = ''
        property_tables  = self.extras.get('tables') or []
        p_tables = len(property_tables) > 0 and property_tables or []
        if not p_tables:
            try:
                product_ids = list(self.products.values_list('id', flat=True))
                skucontrasts = ProductSkuContrast.objects.filter(product__in=product_ids)\
                    .values_list('contrast_detail',flat=True)
                for constrast_detail in skucontrasts:
                    contrast_origin = constrast_detail
                    uni_key = ''.join(sorted(contrast_origin.keys()))
                    if uni_key not in uni_set:
                        uni_set.add(uni_key)
                        p_tables.append({'table': self.format_contrast2table(contrast_origin)})
            except ProductSkuContrast.DoesNotExist:
                logger.warn('ProductSkuContrast not exists:%s' % (constrast_detail))
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
        return {
            'attributes': self.attributes,
            'tables': p_tables,
            'metrics': {
                # 'table':[
                # [u'厚度指数', u'偏薄', u'适中',u'偏厚',u'加厚' ],
                #     [u'弹性指数', u'无弹性', u'微弹性',u'适中', u'强弹性'],
                #     [u'触感指数', u'偏硬', u'柔软', u'适中', u'超柔'],
                # ],
                # 'choices':[2,3,2]
            },
        }

    @classmethod
    def update_schedule_manager_info(cls,
                                     action_user,
                                     sale_product_ids,
                                     upshelf_time,
                                     offshelf_time,
                                     is_topic):
        """
        更新上下架时间和专题类型
        """
        mds = cls.objects.filter(saleproduct__in=sale_product_ids, status=cls.NORMAL)
        for md in mds:
            if md.shelf_status == cls.ON_SHELF:  # 如果是已经上架状态的款式则不去同步时间和专题类型
                continue
            update_fields = []
            if md.onshelf_time != upshelf_time:
                md.onshelf_time = upshelf_time
                update_fields.append('onshelf_time')
            if md.offshelf_time != offshelf_time:
                md.offshelf_time = offshelf_time
                update_fields.append('offshelf_time')
            if md.is_topic != is_topic:
                md.is_topic = is_topic
                update_fields.append('is_topic')
            if update_fields:
                md.save(update_fields=update_fields)
                log_action(action_user, md, CHANGE, u'同步上下架时间和专题类型')

    def update_schedule_detail_info(self, order_weight, is_recommend):
        """
        更新权重和是否推广字段
        """
        update_fields = []
        if self.order_weight != order_weight:
            self.order_weight = order_weight
            update_fields.append('order_weight')
        if self.is_recommend != is_recommend:
            self.is_recommend = is_recommend
            update_fields.append('is_recommend')
        if update_fields:
            self.save(update_fields=update_fields)
            return True

    @classmethod
    def upshelf_right_now_models(cls):
        """需要立即上架的款式"""
        now = datetime.datetime.now()  # 现在时间在上架时间和下架时间之间　状态为正常 处于下架状态
        return cls.objects.filter(
            onshelf_time__lte=now, offshelf_time__gt=now,
            status=cls.NORMAL,
            shelf_status=cls.OFF_SHELF,
            onshelf_time__isnull=False,
            offshelf_time__isnull=False)

    @classmethod
    def offshelf_right_now_models(cls):
        """需要立即下架的款式"""
        now = datetime.datetime.now()  # 下架时间小于现在（在这之前就应该下架）　　状态正常　且处于　上架状态　的　产品
        return cls.objects.filter(
            offshelf_time__lte=now,
            status=cls.NORMAL,
            shelf_status=cls.ON_SHELF)

    def upshelf_model(self):
        """ 上架款式 """
        if self.shelf_status != ModelProduct.ON_SHELF:
            self.shelf_status = ModelProduct.ON_SHELF
            self.save(update_fields=['shelf_status'])
            task_product_upshelf_notify_favorited_customer.delay(self)
            return True
        return False

    def offshelf_model(self):
        """ 下架款式 """
        if self.shelf_status != ModelProduct.OFF_SHELF:
            self.shelf_status = ModelProduct.OFF_SHELF
            self.save(update_fields=['shelf_status'])
            for product in self.products:
                product.offshelf_product()
            if self.is_teambuy:
                product = self.products.first()
                if product:
                    sku = product.prod_skus.first()
                    if sku:
                        from flashsale.pay.models import TeamBuy
                        TeamBuy.end_teambuy(sku)
            return True
        return False

    def update_fields_with_kwargs(self, **kwargs):
        update_fields = []
        for k, v in kwargs.iteritems():
            if hasattr(self, k) and getattr(self, k) != v:
                setattr(self, k, v)
                update_fields.append(k)

        if update_fields:
            self.save(update_fields=update_fields)
            return True

        return False

    def reset_product_shelf_info(self):
        """
        功能：　重置 items product 的上下架信息
        """
        for pro in self.products:
            pro.reset_shelf_info()
        return

    def reset_shelf_info(self):
        """
        功能：　重置上下架时间　和上架状态
        """
        update_fields = []
        if self.shelf_status != ModelProduct.OFF_SHELF:
            self.shelf_status = ModelProduct.OFF_SHELF
            update_fields.append('shelf_status')
        if self.offshelf_time is not None:
            self.offshelf_time = None
            update_fields.append('offshelf_time')
        if self.onshelf_time is not None:
            self.onshelf_time = None
            update_fields.append('onshelf_time')
        if update_fields:
            self.save(update_fields=update_fields)
        self.reset_product_shelf_info()  # 重置产品
        return

    def update_extras(self, extras):
        """ 更新扩展字段 """
        if self.extras != extras:
            self.extras = extras
            self.save(update_fields=['extras'])
            return True
        return False

    def set_lowest_price(self):
        """ 设置款式最低价格 """
        agent_prices = []
        std_sale_price = []
        for pro in self.products:
            skus = pro.normal_skus
            for sku in skus:
                agent_prices.append(sku.agent_price)
                std_sale_price.append(sku.std_sale_price)
        lowest_agent_price = agent_prices and min(agent_prices) or 0  # 递增
        lowest_std_sale_price = std_sale_price and min(std_sale_price) or 0  # 递增
        self.update_fields_with_kwargs(**{
            'lowest_agent_price': lowest_agent_price,
            'lowest_std_sale_price': lowest_std_sale_price
        })

    def set_choose_colors(self):
        """ 更新可选颜色 """
        names = self.products.values('name')
        colors = [cc for cc in set(i['name'].split('/')[-1] for i in names if '/' in i['name'] and i)]
        c = ','.join(colors)
        if not c:
            colors = [i['name'] for i in names]
            c = ','.join(colors)
        if not c:
            return
        extras = self.extras
        extras.setdefault('properties', [])
        properties = extras.get('properties')
        model_properties_d = [{u'可选颜色': c}]
        old_properties_d = dict([(tt['name'], tt['value']) for tt in properties]) if properties else model_properties_d
        old_properties_d.update(model_properties_d[0])
        properties = [{'name': k, "value": v} for k, v in old_properties_d.iteritems()]
        extras.update({'properties': properties})
        self.extras = extras
        self.save(update_fields=['extras'])

    def set_is_flatten(self):
        """
        is_flatten: 平铺展示
        判断： 没有ProductSku或者只有一个则is_fatten = True
        设置： 款式以及款式下的产品is_flatten字段
        """
        products = self.products
        flatten_count = ProductSku.objects.filter(product__in=products).count()
        is_flatten = flatten_count in [0, 1]
        products.update(is_flatten=is_flatten)
        if self.is_flatten != is_flatten:
            self.is_flatten = is_flatten
            self.save(update_fields=['is_flatten'])

    def set_boutique_coupon_only(self, coupon_tpl_id):
        # 设置成精品汇商品返利计划
        self.extras.update({
            "payinfo": {
                "use_coupon_only": True,
                "coupon_template_ids": [int(coupon_tpl_id)]
            }
        })

    def as_boutique_coupon_product(self, coupon_tpl_id):
        sale_infos = self.extras.get('saleinfos', {})
        sale_infos.update({
                "is_coupon_deny": True,
                "per_limit_buy_num": 1000
            })
        self.extras.update({
            "saleinfos": sale_infos,
            "template_id": int(coupon_tpl_id)
        })

    def sale_num(self):
        return None

    def rebet_amount(self):
        return None

    def next_rebet_amount(self):
        return None

    def get_rebate_scheme(self):
        from flashsale.xiaolumm.models.models_rebeta import AgencyOrderRebetaScheme
        return AgencyOrderRebetaScheme.get_rebeta_scheme(self.rebeta_scheme_id)

    def set_shelftime_none(self):
        """
        设置上下架时间为空(排期删除明细特殊场景使用)
        """
        if self.shelf_status == ModelProduct.ON_SHELF:  # 上架状态的产品不予处理
            return
        self.onshelf_time = None
        self.offshelf_time = None
        self.save()

    def to_apimodel(self):
        from apis.v1.products import ModelProduct as APIModel
        data = self.__dict__
        data.update({
            'product_ids': self.products.values_list('id',flat=True),
            'sku_info': self.sku_info,
            'comparison': self.comparison,
            'detail_content': self.detail_content,
        })
        return APIModel(**data)

    @property
    def is_coupon_deny(self):
        """
        功能：　判断是否阻止使用优惠券　True 表示不能使用优惠券　
        """
        saleinfos = self.extras.get('saleinfos') or None
        if saleinfos:
            is_coupon_deny = saleinfos.get('is_coupon_deny') or False
            return is_coupon_deny
        return False


def invalid_apimodelproduct_cache(sender, instance, *args, **kwargs):
    if hasattr(sender, 'API_CACHE_KEY_TPL'):
        logger.debug('invalid_apimodelproduct_cache: %s' % instance.id)
        cache.delete(ModelProduct.API_CACHE_KEY_TPL.format(instance.id))

post_save.connect(invalid_apimodelproduct_cache, sender=ModelProduct,
                  dispatch_uid='post_save_invalid_apimodelproduct_cache')

def update_product_details_info(sender, instance, created, **kwargs):
    """
    同步更新products details
    """
    systemoa = get_systemoa_user()

    def update_pro_shelf_time(upshelf_time, offshelf_time, is_topic):
        # change the item product shelf time and product detail is_sale order_weight and is_recommend in same time
        def _wrapper(p):
            state = p.update_shelf_time(upshelf_time, offshelf_time)
            if state:
                log_action(systemoa, p, CHANGE, u'系统自动同步排期时间')
            if p.detail:
                p.detail.update_weight_and_recommend(is_topic, instance.order_weight, instance.is_recommend)

        return _wrapper

    # 更新产品item Product信息
    try:
        map(update_pro_shelf_time(instance.onshelf_time,
                                  instance.offshelf_time, instance.is_topic), instance.products)
    except Exception as exc:
        logger.error(exc)

post_save.connect(update_product_details_info, sender=ModelProduct,
                  dispatch_uid=u'post_save_update_product_details_info')


def update_product_onshelf_status(sender, instance, created, **kwargs):
    if instance.shelf_status == ModelProduct.OFF_SHELF:
        instance.offshelf_model()
    for product in instance.products:
        if product.type != instance.product_type:
            product.type = instance.product_type
            product.save()


post_save.connect(update_product_onshelf_status, sender=ModelProduct,
                  dispatch_uid=u'post_save_update_product_onshelf_status')


def modelproduct_update_supplier_info(sender, obj, **kwargs):
    pro = obj.item_product
    if isinstance(pro, Product):
        sal_p, supplier = pro.pro_sale_supplier()
        if supplier is not None:
            supplier.total_select_num = F('total_select_num') + 1
            update_model_fields(supplier, update_fields=['total_select_num'])


signal_record_supplier_models.connect(modelproduct_update_supplier_info,
                                      sender=ModelProduct, dispatch_uid='post_save_modelproduct_update_supplier_info')


class ModelProductSkuContrast(BaseModel):
    """ 商品规格尺寸参数 """
    modelproduct = models.OneToOneField(ModelProduct, primary_key=True, related_name='contrast', verbose_name=u'款式ID')
    contrast_detail = JSONCharMyField(max_length=10240, blank=True, verbose_name=u'对照详情')

    class Meta:
        db_table = 'pay_modelproduct_contrast'
        app_label = 'pay'
        verbose_name = u'特卖商品/款式尺码对照表'
        verbose_name_plural = u'特卖商品/款式尺码对照列表'

    def __unicode__(self):
        return u'<%s-%s>' % (self.id, self.modelproduct.id)