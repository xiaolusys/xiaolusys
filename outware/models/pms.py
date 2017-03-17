# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import models
from core.fields import JSONCharMyField

from .base import BaseWareModel
from .. import constants


class OutwareSupplier(BaseWareModel):

    outware_account = models.ForeignKey('outware.OutwareAccount', verbose_name=u'关联账号')

    vendor_code = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'供应商编号')
    vendor_name = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'供应商名称')

    uni_key = models.CharField(max_length=128, unique=True, verbose_name=u'唯一标识' )
    extras  = JSONCharMyField(max_length=1024, default={}, verbose_name=u'附加信息')

    class Meta:
        db_table = 'outware_supplier'
        app_label = 'outware'
        verbose_name = u'外仓/对接供应商'
        verbose_name_plural = u'外仓/对接供应商'

    @classmethod
    def generate_unikey(cls, account_id, vdr_code):
        return '{vendor_code}-{account_id}'.format(vendor_code=vdr_code, account_id=account_id)


class OutwareSku(BaseWareModel):
    """ 商品信息直接跟供应商关联 """

    outware_supplier = models.ForeignKey(OutwareSupplier, verbose_name=u'关联供应商')

    sku_code = models.CharField(max_length=64, db_index=True, verbose_name=u'内部SKU编号')
    ware_sku_code = models.CharField(max_length=64, db_index=True, verbose_name=u'外部SKU编号')

    is_unioned = models.BooleanField(default=False, verbose_name=u'是否同步供应商与sku关系')
    uni_key = models.CharField(max_length=128, unique=True, verbose_name=u'唯一标识')
    extras = JSONCharMyField(max_length=1024, default={}, verbose_name=u'附加信息') #商品的基础资料及款式信息

    class Meta:
        db_table = 'outware_sku'
        app_label = 'outware'
        verbose_name = u'外仓/对接商品SKU'
        verbose_name_plural = u'外仓/对接商品SKU'

    @classmethod
    def generate_unikey(self, supplier_id, sku_code):
        return '{sku_code}-{supplier_id}'.format(sku_code=sku_code, supplier_id=supplier_id)

    def set_ware_sku_code(self, ware_sku_code):
        self.ware_sku_code = ware_sku_code

    def finish_unioned(self):
        self.is_unioned =True



class OutwareInboundOrder(BaseWareModel):

    ORDER_TYPE_CHOICES = ((s['code'], s['name']) for s in [constants.ORDER_PURCHASE, constants.ORDER_REFUND])

    STATUS_CHOICES = (
        (constants.NORMAL, '新建'),
        (constants.RECEIVED, '接收'),
        (constants.ARRIVED, '到仓'),
        (constants.CANCEL, '取消'),
    )

    outware_supplier = models.ForeignKey(OutwareSupplier, verbose_name=u'关联供应商')

    inbound_code = models.CharField(max_length=64, db_index=True, verbose_name=u'入仓单/销退入仓编号')
    store_code  = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'外部仓库编号')

    order_type = models.IntegerField( db_index=True, choices=ORDER_TYPE_CHOICES, verbose_name=u'单据类型')

    status  = models.SmallIntegerField(db_index=True, default=constants.NORMAL,
                                       choices=STATUS_CHOICES, verbose_name='订单状态')

    uni_key = models.CharField(max_length=128, unique=True, verbose_name=u'唯一标识')
    extras = JSONCharMyField(max_length=10240, default={}, verbose_name=u'附加信息') #商品的基础资料及款式信息

    class Meta:
        db_table = 'outware_inbound'
        app_label = 'outware'
        verbose_name = u'外仓/推送入仓单'
        verbose_name_plural = u'外仓/推送入仓单'

    @classmethod
    def generate_unikey(self, account_id, inbound_code, store_code, order_type):
        return '{inbound_code}-{store_code}-{order_type}-{account_id}'.format(
            inbound_code=inbound_code,
            store_code=store_code,
            order_type=order_type,
            account_id=account_id,
        )

    def change_order_status(self, status_code):
        if self.status < int(status_code):
            self.status = status_code
            self.save()
            return True
        return False


class OutwareInboundSku(BaseWareModel):

    outware_inboind = models.ForeignKey(OutwareInboundOrder, verbose_name=u'关联推送入仓单')

    sku_code = models.CharField(max_length=64, db_index=True, verbose_name=u'内部SKU编号')

    batch_no = models.CharField(max_length=32, db_index=True, verbose_name=u'批次号')
    push_qty = models.IntegerField(default=0, verbose_name=u'入仓创建数量')

    pull_good_qty = models.IntegerField(default=0, verbose_name=u'外仓入仓良品数')
    pull_bad_qty = models.IntegerField(default=0, verbose_name=u'外仓入仓次品数')

    uni_key = models.CharField(max_length=128, unique=True, verbose_name=u'唯一标识')
    extras = JSONCharMyField(max_length=1024, default={}, verbose_name=u'附加信息') #商品的基础资料及款式信息

    class Meta:
        db_table = 'outware_inboundsku'
        app_label = 'outware'
        verbose_name = u'外仓/推送入仓SKU'
        verbose_name_plural = u'外仓/推送入仓SKU'

    @classmethod
    def generate_unikey(self, inbound_id, sku_code, batch_no):
        return '{batch_no}-{sku_code}-{inbound_id}'.format(
            inbound_id=inbound_id,
            sku_code=sku_code,
            batch_no=batch_no,
        )



