# -*- coding:utf-8 -*-
import datetime
import operator
from django.db import models
from django.db.models import Q

from core.models import BaseModel
from core.managers import BaseManager
from shopback.items.models import Product,ProductSku

import logging
logger = logging.getLogger(__name__)

class LackGoodOrderManager(BaseManager):

    def get_objects_by_order_ids(self, order_ids):
        if not order_ids:
            return self.get_queryset().none()
        filter_q = reduce(operator.or_, (Q(order_group_key__contains='-%s-'%x) for x in order_ids))
        return self.get_queryset().filter(filter_q).filter(status=self.model.NORMAL)


class LackGoodOrder(BaseModel):

    NORMAL = 'normal'
    DELETE = 'delete'
    STATUS_CHOICES = (
        (NORMAL, u'正常'),
        (DELETE, u'作废'),
    )

    supplier = models.ForeignKey('supplier.SaleSupplier',
                                 related_name='lackgood_manager',
                                 verbose_name=u'供应商')
    product_id = models.IntegerField(db_index=True, verbose_name=u'商品ID')
    sku_id = models.IntegerField(db_index=True, verbose_name=u'规格ID')
    lack_num = models.IntegerField(default=0, verbose_name=u'缺货数量')

    refund_num = models.IntegerField(default=0, verbose_name=u'退款数量')
    is_refund = models.BooleanField(default=False, verbose_name=u'已退款')
    refund_time = models.DateTimeField(blank=True,null=True,db_index=True,verbose_name=u'退款时间')

    order_group_key = models.CharField(max_length=64,verbose_name=u'订货单组主键')
    status = models.CharField(max_length=8 ,choices=STATUS_CHOICES,default=NORMAL ,verbose_name=u'状态')

    creator = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'创建者')
    objects = LackGoodOrderManager()

    class Meta:
        db_table = 'flashsale_dinghuo_lackorder'
        app_label = 'dinghuo'
        unique_together = ['order_group_key','sku_id']
        verbose_name = u'订货缺货商品'
        verbose_name_plural = u'订货缺货商品列表'

    def delete(self, using=None):
        self.status = self.DELETE
        self.save()

    @property
    def product(self):
        return Product.objects.filter(id=self.product_id).first()

    @property
    def product_sku(self):
        return ProductSku.objects.filter(id=self.sku_id).first()

    @property
    def is_canceled(self):
        return self.status == self.DELETE

    def get_refundable(self):
        return self.lack_num > self.refund_num





