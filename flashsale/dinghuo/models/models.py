# -*- coding:utf-8 -*-
import datetime
import re
import sys
import copy
import numpy as np
from django.db import models
from django.db.models import Sum, Count, F, Q
from django.db.models.signals import post_save, pre_save
from django.contrib.auth.models import User
from django.db import transaction

from core.utils.modelutils import update_model_fields
from core.fields import JSONCharMyField
from core.models import BaseModel
from shopback.items.models import ProductSku, Product, SkuStock
from shopback.refunds.models import Refund
from supplychain.supplier.models import SaleSupplier, SaleProduct
from .purchase_order import OrderList, OrderDetail
import logging

logger = logging.getLogger(__name__)

class ProductSkuDetail(models.Model):
    product_sku = models.BigIntegerField(unique=True, verbose_name=u'库存商品规格')
    exist_stock_num = models.IntegerField(default=0, verbose_name=u'上架前库存')
    sample_num = models.IntegerField(default=0, verbose_name=u'样品数量')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'生成日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        db_table = 'flash_sale_product_sku_detail'
        app_label = 'dinghuo'
        verbose_name = u'特卖商品库存'
        verbose_name_plural = u'特卖商品库存列表'

    def __unicode__(self):
        return u'<%s>' % (self.product_sku)


from shopback import signals


def init_stock_func(sender, product_list, *args, **kwargs):
    import datetime
    from django.db.models import Sum
    today = datetime.date.today()

    for pro_bean in product_list:
        sku_qs = pro_bean.prod_skus.all()
        for sku_bean in sku_qs:
            total_num = OrderDetail.objects.filter(
                chichu_id=sku_bean.id,
                orderlist__created__range=
                (today - datetime.timedelta(days=7), today)).exclude(
                orderlist__status=OrderList.ZUOFEI).aggregate(
                total_num=Sum('arrival_quantity')).get('total_num') or 0
            pro_sku_beans = ProductSkuDetail.objects.get_or_create(
                product_sku=sku_bean.id)
            pro_sku_bean = pro_sku_beans[0]
            result_num = sku_bean.quantity - sku_bean.wait_post_num - total_num
            pro_sku_bean.exist_stock_num = result_num if result_num > 0 else 0
            pro_sku_bean.sample_num = 0
            sku_bean.memo = ""
            sku_bean.save()
            pro_sku_bean.save()


signals.signal_product_upshelf.connect(init_stock_func, sender=Product)


class SaleInventoryStat(models.Model):
    """
    （只统计小鹿特卖商品）统计当天的订货表的新增采购数，未到货总数，到货数，发出件数，总库存数
    """
    CHILD = 1
    FEMALE = 2

    INVENTORY_CATEGORY = ((CHILD, u'童装'), (FEMALE, u'女装'))
    newly_increased = models.IntegerField(default=0, verbose_name=u'新增采购数')
    not_arrive = models.IntegerField(default=0, verbose_name=u'未到货数')
    arrived = models.IntegerField(default=0, verbose_name=u'到货数')
    deliver = models.IntegerField(default=0, verbose_name=u'发出数')
    inventory = models.IntegerField(default=0, verbose_name=u'库存')
    category = models.IntegerField(blank=True,
                                   null=True,
                                   db_index=True,
                                   choices=INVENTORY_CATEGORY,
                                   verbose_name=u'分类')
    stat_date = models.DateField(verbose_name=u'统计日期')

    class Meta:
        db_table = 'flashsale_inventory_stat'
        app_label = 'dinghuo'
        verbose_name = u'特卖入库及库存每日统计'
        verbose_name_plural = u'特卖入库及库存每日统计列表'

    def __unicode__(self):
        return u'<%s>' % self.stat_date
