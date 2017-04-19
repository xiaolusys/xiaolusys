# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import models, transaction

from core.fields import JSONCharMyField
from .base import BaseWareModel
from .. import constants
from shopback.outware.utils import action_decorator
from shopback.outware.adapter.ware.push import runner
import logging
logger = logging.getLogger(__name__)


class OutwareOrder(BaseWareModel):
    """ 实际推送给外仓的组合销售订单 """

    DEFAULT_ORDER_TYPE = constants.ORDER_TYPE_USUAL['code']
    ORDER_TYPE_CHOICES = ((s['code'], s['name']) for s in [
        constants.ORDER_TYPE_USUAL,
        constants.ORDER_TYPE_CROSSBOADER,
        constants.ORDER_TYPE_BOOKING,
    ])

    DEFAULT_ORDER_SOURCE= constants.ORDER_SALE['code']
    ORDER_SOURCE_CHOICES = ((s['code'], s['name']) for s in [
        constants.ORDER_RETURN,
        constants.ORDER_SALE,
    ])

    STATUS_CHOICES = (
        (constants.NORMAL,   '待推送'),
        (constants.RECEIVED, '已接单'),
        (constants.LACKGOODS, '订单缺货'),
        (constants.PACKING, '打包中'),
        (constants.LOADING, '装车中'),
        (constants.SENDED,  '已发货'),
        (constants.CANCEL,   '取消'),
    )

    outware_account = models.ForeignKey('outware.OutwareAccount', verbose_name=u'关联账号')

    order_type = models.IntegerField(db_index=True, choices=ORDER_TYPE_CHOICES, default=DEFAULT_ORDER_TYPE, verbose_name=u'订单类型')
    order_source = models.IntegerField(db_index=True, choices=ORDER_SOURCE_CHOICES, default=DEFAULT_ORDER_SOURCE, verbose_name=u'订单来源')
    store_code = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'外部仓库编号')
    union_order_code = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'组合订单编号')

    status = models.SmallIntegerField(db_index=True, default=constants.NORMAL,
                                      choices=STATUS_CHOICES, verbose_name='订单状态')
    uni_key = models.CharField(max_length=128, unique=True, verbose_name=u'唯一标识' )
    extras  = JSONCharMyField(max_length=1024, default={}, verbose_name=u'附加信息')

    class Meta:
        db_table = 'outware_order'
        app_label = 'outware'
        verbose_name = u'外仓/推送订单'
        verbose_name_plural = u'外仓/推送订单'

    @classmethod
    def generate_unikey(self, account_id, order_code, order_type):
        return '{order_code}-{order_type}-{account_id}'.format(
            order_code=order_code, order_type=order_type, account_id=account_id)

    @property
    def order_skus(self):
        return OutwareOrderSku.objects.filter(union_order_code=self.union_order_code, is_valid=True)

    @property
    def is_reproducible(self):
        return self.status in (constants.NORMAL, constants.CANCEL)

    def change_order_status(self, status_code):
        self.status = status_code
        self.save()

        if status_code == constants.CANCEL:
            for order_sku in self.order_skus:
                order_sku.set_invalid()
                order_sku.save()


class OutwareOrderSku(BaseWareModel):
    """ 实际推送给外仓的组合销售订单sku """

    outware_account = models.ForeignKey('outware.OutwareAccount', verbose_name=u'关联账号')

    union_order_code = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'关联组合订单编号')

    origin_skuorder_no  = models.CharField(max_length=32, db_index=True, verbose_name=u'原始SKU订单编号')

    sku_code = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'内部SKU编号')
    sku_qty  = models.IntegerField(default=0, verbose_name=u'推送订单SKU数量')

    is_valid  = models.BooleanField(default=True, db_index=True, verbose_name=u'是否有效')

    uni_key = models.CharField(max_length=128, unique=True, verbose_name=u'唯一标识' )
    extras  = JSONCharMyField(max_length=1024, default={}, verbose_name=u'附加信息')

    class Meta:
        db_table = 'outware_ordersku'
        app_label = 'outware'
        verbose_name = u'外仓/推送订单sku'
        verbose_name_plural = u'外仓/推送订单sku'

    @classmethod
    def generate_unikey(self, account_id, origin_skuorder_no):
        return '{origin_skuorder_no}-{account_id}'.format(origin_skuorder_no=origin_skuorder_no, account_id=account_id)

    def set_invalid(self):
        self.is_valid = False

    def set_valid(self):
        self.is_valid = True

    @property
    def is_reproducible(self):
        return self.is_valid == False


class OutwarePackage(BaseWareModel):
    """ 外仓实际发货包裹(含销售订单/退仓单) """

    PACKAGE_TYPE_CHOICES = ((s['code'], s['name']) for s in [constants.ORDER_SALE, constants.ORDER_RETURN])

    outware_account = models.ForeignKey('outware.OutwareAccount', verbose_name=u'关联账号')

    package_type = models.CharField(max_length=16, db_index=True, choices=PACKAGE_TYPE_CHOICES, verbose_name=u'包裹类型')
    package_order_code = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'销单/退仓单编号')

    store_code = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'外部仓库编号')
    logistics_no = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'快递单号')
    carrier_code = models.CharField(max_length=20, blank=True, db_index=True, verbose_name=u'快递公司编码')

    uni_key = models.CharField(max_length=128, unique=True, verbose_name=u'唯一标识' )
    extras  = JSONCharMyField(max_length=512, default={}, verbose_name=u'附加信息')

    class Meta:
        db_table = 'outware_package'
        app_label = 'outware'
        verbose_name = u'外仓/发送包裹'
        verbose_name_plural = u'外仓/发送包裹'

    @classmethod
    def generate_unikey(self, account_id, logistics_no, carrier_code):
        return '{logistics_no}-{carrier_code}-{account_id}'.format(
            logistics_no=logistics_no, carrier_code=carrier_code, account_id=account_id)

    def get_sku_dict(self):
        return {skuitem.sku_code: skuitem.sku_qty for skuitem in self.outwarepackagesku_set.all()}

    @staticmethod
    def create_by_push_info(order_code, order_type, dict_obj):
        """ 包含入仓单/销退单到仓确认 """
        from shopback.outware.models.wareauth import OutwareAccount
        ware_account = OutwareAccount.get_fengchao_account()
        ow_packages = []
        with transaction.atomic():
            for package in dict_obj.packages:
                # firstly, update outware package status and sku qty
                ow_package, state = OutwarePackage.objects.get_or_create(
                    outware_account=ware_account,
                    carrier_code=package.carrier_code,
                    logistics_no=package.logistics_no,
                    uni_key=OutwarePackage.generate_unikey(ware_account.id, package.logistics_no, package.carrier_code)
                )
                # 忽略重复单
                if not state:
                    continue
                ow_package.package_order_code = order_code
                ow_package.package_type = order_type
                ow_package.store_code   = package.store_code
                ow_package.save()

                for item in package.package_items:
                    OutwarePackageSku.objects.create(
                        package=ow_package,
                        sku_code=item.sku_code,
                        batch_no=item.batch_no,
                        sku_qty=item.sku_qty,
                        uni_key=OutwarePackageSku.generate_unikey(item.sku_code, item.batch_no, ow_package.id)
                    )
                ow_packages.append(ow_package)
        ow_packages = runner.get_runner(order_type)(ow_packages).execute()
        return ow_packages


class OutwarePackageSku(BaseWareModel):
    """ 外仓实际发货包裹SKU """

    package = models.ForeignKey(OutwarePackage, verbose_name=u'关联包裹')

    origin_skuorder_no = models.CharField(max_length=32, db_index=True,
                                          verbose_name=u'原始SKU订单编号',
                                          help_text=u'该字段存在争议暂不使用')

    sku_code = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'内部SKU编号')
    batch_no = models.CharField(max_length=32, db_index=True, verbose_name=u'批次号')
    sku_qty = models.IntegerField(default=0, verbose_name=u'推送订单SKU数量')

    uni_key = models.CharField(max_length=128, unique=True, verbose_name=u'唯一标识' )
    extras  = JSONCharMyField(max_length=512, default={}, verbose_name=u'附加信息')

    class Meta:
        db_table = 'outware_packagesku'
        app_label = 'outware'
        verbose_name = u'外仓/发送包裹sku'
        verbose_name_plural = u'外仓/发送包裹sku'

    @classmethod
    def generate_unikey(self, sku_code, batch_no, package_id):
        return '{sku_code}-{batch_no}-{package_id}'.format(
            sku_code=sku_code, batch_no=batch_no, package_id=package_id)

