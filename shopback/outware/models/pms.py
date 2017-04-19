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

    def __unicode__(self):
        return '<%s, %s>'%(self.id, self.vendor_code)

    @classmethod
    def generate_unikey(cls, account_id, vdr_code):
        return '{vendor_code}-{account_id}'.format(vendor_code=vdr_code, account_id=account_id)

    @property
    def is_pushed_ok(self):
        return self.is_action_success(constants.ACTION_SUPPLIER_CREATE['code'])

class OutwareSku(BaseWareModel):
    """ 商品信息直接跟供应商关联 """

    SKU_TYPE_CHOICES = ((s['code'], s['name']) for s in [
        constants.SKU_TYPE_PRODUCT,
        constants.SKU_TYPE_GIFTS,
        constants.SKU_TYPE_METARIAL,
    ])

    DECLARE_TYPE_CHOICES = ((s['code'], s['name']) for s in [
        constants.DECLARE_TYPE_NONE,
        constants.DECLARE_TYPE_BOUND,
        constants.DECLARE_TYPE_DIRECT,
    ])

    outware_supplier = models.ForeignKey(OutwareSupplier, verbose_name=u'关联供应商')

    sku_code = models.CharField(max_length=64, db_index=True, verbose_name=u'内部SKU编号')
    ware_sku_code = models.CharField(max_length=64, db_index=True, verbose_name=u'外部SKU编号')

    sku_type  = models.IntegerField(default=constants.SKU_TYPE_PRODUCT['code'], choices=SKU_TYPE_CHOICES,
                                    db_index=True, verbose_name=u'SKU类型')

    declare_type = models.IntegerField(default=constants.DECLARE_TYPE_NONE['code'], choices=DECLARE_TYPE_CHOICES,
                                    db_index=True, verbose_name=u'报关类型')

    is_batch_mgt  = models.BooleanField(default=False, verbose_name=u'是否启用批次管理', help_text=u'支持批次先到先出')
    is_expire_mgt = models.BooleanField(default=False, verbose_name=u'是否启用有效期管理', help_text=u'支持商品过期不能出单')
    is_vendor_mgt = models.BooleanField(default=False, verbose_name=u'是否启用供应商管理', help_text=u'支持同SKU多供应商供货')
    is_unioned    = models.BooleanField(default=False, verbose_name=u'关联供应商', help_text=u'是否同步供应商与sku关系')

    uni_key = models.CharField(max_length=128, unique=True, verbose_name=u'唯一标识')
    extras = JSONCharMyField(max_length=1024, default={}, verbose_name=u'附加信息') #商品的基础资料及款式信息

    class Meta:
        db_table = 'outware_sku'
        app_label = 'outware'
        verbose_name = u'外仓/对接商品SKU'
        verbose_name_plural = u'外仓/对接商品SKU'

    def __unicode__(self):
        return '<%s, %s>' % (self.outware_supplier, self.sku_code)

    @classmethod
    def generate_unikey(self, supplier_id, sku_code):
        return '{sku_code}-{supplier_id}'.format(sku_code=sku_code, supplier_id=supplier_id)

    @property
    def is_batch_mgt_on(self):
        return self.is_batch_mgt

    @property
    def is_expire_mgt_on(self):
        return self.is_expire_mgt

    @property
    def is_vendor_mgt_on(self):
        return self.is_vendor_mgt

    @property
    def shelf_life_days(self):
        return self.extras.get('data', {}).get('shelf_life', 0)

    def set_ware_sku_code(self, ware_sku_code):
        self.ware_sku_code = ware_sku_code

    @property
    def is_pushed_ok(self):
        from .wms import OutwareSkuStock
        ow_skustock = OutwareSkuStock.objects.filter(sku_code=self.sku_code).first()
        return ow_skustock and ow_skustock.is_action_success(constants.ACTION_SKU_CREATE['code']) or False

    def finish_unioned(self):
        self.is_unioned =True



class OutwareInboundOrder(BaseWareModel):

    ORDER_PURCHASE = constants.ORDER_PURCHASE['code']
    ORDER_REFUND = constants.ORDER_REFUND['code']
    ORDER_TYPE_CHOICES = ((s['code'], s['name']) for s in [constants.ORDER_PURCHASE, constants.ORDER_REFUND])

    NORMAL = constants.NORMAL
    STATUS_CHOICES = (
        (constants.NORMAL, '未推送'),
        (constants.RECEIVED, '已接收'),
        (constants.ARRIVED, '已到仓'),
        (constants.CANCEL, '已取消'),
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

    def __unicode__(self):
        return '<%s, %s>' % (self.outware_supplier, self.inbound_code)

    @classmethod
    def generate_unikey(self, inbound_code, order_type):
        return '{inbound_code}-{order_type}'.format(
            inbound_code=inbound_code,
            order_type=order_type,
        )

    @property
    def is_pushed_ok(self):
        return self.status in (constants.RECEIVED, constants.ARRIVED)

    @property
    def is_reproducible(self):
        return self.status in (constants.NORMAL, constants.CANCEL)

    def change_order_status(self, status_code):
        self.status = status_code
        self.save()


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

    def __unicode__(self):
        return '<inbound_id:%s, %s>' % (self.outware_inboind_id, self.sku_code)

    @classmethod
    def generate_unikey(self, inbound_id, sku_code, batch_no):
        return '{batch_no}-{sku_code}-{inbound_id}'.format(
            inbound_id=inbound_id,
            sku_code=sku_code,
            batch_no=batch_no,
        )



