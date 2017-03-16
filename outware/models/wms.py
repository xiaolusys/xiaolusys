# coding: utf8
from __future__ import absolute_import, unicode_literals

# TODO@MERON 库存调整记录，商品库存信息
from django.db import models
from core.fields import JSONCharMyField
from .base import BaseWareModel

class OutwareSkuStock(BaseWareModel):
    """ 商品库存需要跟具体的批次号关联 """
    outware_supplier = models.ForeignKey('outware.OutwareSupplier', verbose_name=u'关联供应商')

    batch_no = models.CharField(max_length=32, db_index=True, verbose_name=u'批次号')
    sku_code = models.CharField(max_length=64, db_index=True, verbose_name=u'内部SKU编号')
    store_code = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'外部仓库编号')

    push_sku_good_qty  = models.IntegerField(default=0, verbose_name=u'发给外仓SKU良品数', help_text=u'根据入仓实际收货良品数量累加')
    push_sku_bad_qty = models.IntegerField(default=0, verbose_name=u'发给外仓SKU次品数', help_text=u'根据入仓实际收货次品数量累加')

    pull_good_available_qty = models.IntegerField(default=0, verbose_name=u'外仓可分配良品数')
    pull_good_lock_qty = models.IntegerField(default=0, verbose_name=u'外仓已锁定良品数')
    pull_bad_qty = models.IntegerField(default=0, verbose_name=u'外仓次品数')

    uni_key = models.CharField(max_length=128, unique=True, verbose_name=u'唯一标识')
    extras = JSONCharMyField(max_length=5012, default={}, verbose_name=u'附加信息') #商品的基础资料及款式信息

    class Meta:
        db_table = 'outware_skustock'
        app_label = 'outware'
        verbose_name = u'外仓/对接商品SKU库存'
        verbose_name_plural = u'外仓/对接商品SKU库存'

    @classmethod
    def generate_unikey(self, supplier_id, store_code, sku_code, batch_no):
        return '{batch_no}-{store_code}-{sku_code}-{supplier_id}'.format(
            batch_no=batch_no,
            sku_code=sku_code,
            store_code=store_code,
            supplier_id=supplier_id,
        )

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

