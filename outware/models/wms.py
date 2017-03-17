# coding: utf8
from __future__ import absolute_import, unicode_literals

# TODO@MERON 库存调整记录，商品库存信息
import datetime
from django.db import models, transaction
from core.fields import JSONCharMyField
from .base import BaseWareModel

class OutwareSkuStock(BaseWareModel):
    """ 商品库存需要跟具体的批次号关联 """

    sku_code = models.CharField(max_length=64, unique=True, verbose_name=u'内部SKU编号')

    push_sku_good_qty  = models.IntegerField(default=0, verbose_name=u'发给外仓SKU良品数', help_text=u'根据入仓实际收货良品数量累加')
    push_sku_bad_qty = models.IntegerField(default=0, verbose_name=u'发给外仓SKU次品数', help_text=u'根据入仓实际收货次品数量累加')

    pull_good_available_qty = models.IntegerField(default=0, verbose_name=u'外仓可分配良品总数')
    pull_good_lock_qty = models.IntegerField(default=0, verbose_name=u'外仓已锁定良品总数')
    pull_bad_qty = models.IntegerField(default=0, verbose_name=u'外仓次品总数')

    paid_num    = models.IntegerField(default=0, verbose_name=u'付款数量')
    package_num = models.IntegerField(default=0, verbose_name=u'发货数量')
    refund_num  = models.IntegerField(default=0, verbose_name=u'退货数量')
    adjust_num  = models.IntegerField(default=0, verbose_name=u'调整数量', help_text=u'跟库存调整值关联')

    last_pull_time = models.DateTimeField(null=False, default=datetime.datetime.now, db_index=True, verbose_name=u'库存最后更新日期')

    class Meta:
        db_table = 'outware_skustock'
        app_label = 'outware'
        verbose_name = u'外仓/对接商品SKU库存'
        verbose_name_plural = u'外仓/对接商品SKU库存'

    def set_good_available_qty(self, good_qty):
        self.pull_good_available_qty = good_qty

    def minus_good_available_qty(self, good_qty):
        self.pull_good_available_qty -= good_qty

    def plus_good_available_qty(self, good_qty):
        self.pull_good_available_qty += good_qty

    def minus_bad_qty(self, bad_qty):
        self.pull_bad_qty -= bad_qty

    def plus_bad_qty(self, bad_qty):
        self.pull_bad_qty += bad_qty

    # @classmethod
    # def update_skustock_num(cls, update_type, sku_code, paid_num):
    #
    #     out_sku, state = OutwareSkuStock.objects.get_or_create(sku_code=sku_code)








