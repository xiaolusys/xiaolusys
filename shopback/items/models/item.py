# coding: utf-8
from __future__ import unicode_literals

import collections
import datetime
import json

from django.db import models
from shopapp.taobao import apis
from shopback import paramconfig as pcfg

import logging

logger = logging.getLogger(__name__)


class Item(models.Model):
    """ 淘宝线上商品 """
    APPROVE_STATUS = (
        (pcfg.ONSALE_STATUS, u'在售'),
        (pcfg.INSTOCK_STATUS, u'库中'),
    )

    num_iid = models.CharField(primary_key=True, max_length=64, verbose_name='商品ID')
    user = models.ForeignKey('users.User', null=True, related_name='items', verbose_name='店铺')
    category = models.ForeignKey('categorys.Category', null=True, related_name='items', verbose_name='淘宝分类')
    product = models.ForeignKey('items.Product', null=True, related_name='items', verbose_name='关联库存商品')

    outer_id = models.CharField(max_length=64, blank=True, verbose_name='外部编码')
    num = models.IntegerField(null=True, verbose_name='数量')
    sync_stock = models.BooleanField(default=True, verbose_name='库存同步')

    seller_cids = models.CharField(max_length=126, blank=True, verbose_name='卖家分类')
    approve_status = models.CharField(max_length=20, choices=APPROVE_STATUS, blank=True,
                                      verbose_name='在售状态')  # onsale,instock
    type = models.CharField(max_length=12, blank=True, verbose_name='商品类型')
    valid_thru = models.IntegerField(null=True, verbose_name='有效期')

    with_hold_quantity = models.IntegerField(default=0, verbose_name='拍下未付款数')
    delivery_time = models.DateTimeField(null=True, blank=True, verbose_name='发货时间')

    price = models.CharField(max_length=12, blank=True, verbose_name='价格')
    postage_id = models.BigIntegerField(null=True, verbose_name='运费模板ID')

    has_showcase = models.BooleanField(default=False, verbose_name='橱窗推荐')
    modified = models.DateTimeField(null=True, blank=True, verbose_name='修改时间')

    list_time = models.DateTimeField(null=True, blank=True, verbose_name='上架时间')
    delist_time = models.DateTimeField(null=True, blank=True, verbose_name='下架时间')

    has_discount = models.BooleanField(default=False, verbose_name='有折扣')

    props = models.TextField(blank=True, verbose_name='商品属性')
    title = models.CharField(max_length=148, blank=True, verbose_name='商品标题')
    property_alias = models.TextField(blank=True, verbose_name='自定义属性')

    has_invoice = models.BooleanField(default=False, verbose_name='有发票')
    pic_url = models.URLField(blank=True, verbose_name='商品图片')
    detail_url = models.URLField(blank=True, verbose_name='详情链接')

    last_num_updated = models.DateTimeField(null=True, blank=True, verbose_name='最后库存同步日期')  # 该件商品最后库存同步日期

    desc = models.TextField(blank=True, verbose_name='商品描述')
    skus = models.TextField(blank=True, verbose_name='规格')
    status = models.BooleanField(default=True, verbose_name='使用')

    class Meta:
        db_table = 'shop_items_item'
        app_label = 'items'
        verbose_name = u'线上商品'
        verbose_name_plural = u'线上商品列表'

    def __unicode__(self):
        return '<%s,%s,%s>' % (self.num_iid, self.outer_id, self.title)

    @property
    def sku_list(self):
        try:
            return json.loads(self.skus)
        except:
            return {}

    @property
    def property_alias_dict(self):
        property_list = self.property_alias.split(';')
        property_dict = {}
        for p in property_list:
            if p:
                r = p.split(':')
                property_dict['%s:%s' % (r[0], r[1])] = r[2]
        return property_dict

    @classmethod
    def get_or_create(cls, user_id, num_iid, force_update=False):
        item, state = Item.objects.get_or_create(num_iid=num_iid)
        if state or force_update:
            try:
                response = apis.taobao_item_get(num_iid=num_iid, tb_user_id=user_id)
                item_dict = response['item_get_response']['item']
                item = Item.save_item_through_dict(user_id, item_dict)

            except Exception, exc:
                logger.error('商品更新出错(num_iid:%s)' % str(num_iid), exc_info=True)
        return item

    @classmethod
    def save_item_through_dict(cls, user_id, item_dict):
        from shopback.categorys.models import Category
        from .product import Product
        category = Category.get_or_create(user_id, item_dict['cid'])
        if item_dict.has_key('outer_id') and item_dict['outer_id']:
            products = Product.objects.filter(outer_id=item_dict['outer_id'])
            product = None
            if products.count() > 0:
                product = products[0]
                product.name = product.name or item_dict['title']
                product.pic_path = product.pic_path or item_dict['pic_url']
                product.save()
        else:
            # logger.warn('item has no outer_id(num_iid:%s)'%str(item_dict['num_iid']))
            product = None

        item, state = cls.objects.get_or_create(num_iid=item_dict['num_iid'])
        skus = item_dict.get('skus', None)
        item_dict['skus'] = skus and skus or item.skus
        for k, v in item_dict.iteritems():
            hasattr(item, k) and setattr(item, k, v)

        if not item.last_num_updated:
            item.last_num_updated = datetime.datetime.now()

        item.user = User.objects.get(visitor_id=user_id)
        item.product = product
        item.category = category
        item.status = True
        item.save()
        return item


class SkuProperty(models.Model):
    """
        规格属性
    """
    PRODUCT_STATUS = (
        (pcfg.NORMAL, u'使用'),
        (pcfg.DELETE, u'作废'),
    )

    num_iid = models.BigIntegerField(verbose_name='商品ID')
    sku_id = models.BigIntegerField(verbose_name='规格ID')
    outer_id = models.CharField(max_length=32, null=True, blank=True, verbose_name='编码')

    properties_name = models.CharField(max_length=512, null=True, blank=True, verbose_name='规格名称')
    properties = models.CharField(max_length=512, null=True, blank=True, verbose_name='规格')
    created = models.DateTimeField(null=True, blank=True, verbose_name='创建日期')

    with_hold_quantity = models.IntegerField(default=0, verbose_name='拍下未付款数')
    sku_delivery_time = models.DateTimeField(null=True, blank=True, verbose_name='发货时间')

    modified = models.DateTimeField(null=True, blank=True, verbose_name='修改日期')
    price = models.FloatField(default=0.0, verbose_name='价格')

    quantity = models.IntegerField(default=0, verbose_name='数量')
    status = models.CharField(max_length=10, blank=True, choices=PRODUCT_STATUS, verbose_name='状态')

    class Meta:
        db_table = 'shop_items_skuproperty'
        unique_together = ("num_iid", "sku_id")
        app_label = 'items'
        verbose_name = u'线上商品规格'
        verbose_name_plural = u'线上商品规格列表'

    @property
    def properties_alias(self):
        return ''.join([p.split(':')[3] for p in self.properties_name.split(';') if p])

    @classmethod
    def save_or_update(cls, sku_dict):

        sku, state = cls.objects.get_or_create(num_iid=sku_dict.pop('num_iid'),
                                               sku_id=sku_dict.pop('sku_id'))
        for k, v in sku_dict.iteritems():
            if k == 'outer_id' and not v: continue
            hasattr(sku, k) and setattr(sku, k, v)
        sku.save()
        return sku
