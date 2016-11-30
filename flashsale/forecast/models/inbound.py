# coding=utf-8
import datetime
import random
from django.db import models
from django.db.models.signals import post_save

from core.models import BaseModel
from core.utils.unikey import uniqid
from supplychain.supplier.models import SaleSupplier

from .. import constants


def default_inbound_ware_no():
    return datetime.datetime.now().strftime('%Y%m%d') + '-1'


class RealInbound(BaseModel):

    STAGING = 'staging'
    COMPLETED = 'completed'
    # CHECKED  = 'checked'
    CANCELED = 'canceled'

    STATUS_CHOICES = ((STAGING, u'待入库'), (COMPLETED, u'已入库'),(CANCELED, u'已取消'))

    wave_no = models.CharField(max_length=32, default=default_inbound_ware_no,
                               db_index=True, verbose_name=u'入库批次')

    forecast_inbound = models.ForeignKey('forecast.ForecastInbound',  related_name='real_inbound_manager',
                                         null=True, verbose_name=u'关联预测到货单')
    relate_order_set = models.ManyToManyField('dinghuo.OrderList', related_name='real_inbounds',
                                         verbose_name=u'关联订货单')

    total_inbound_num = models.IntegerField(default=0, verbose_name=u'总入仓数')
    total_inferior_num = models.IntegerField(default=0, verbose_name=u'总次品数')

    supplier = models.ForeignKey(SaleSupplier, verbose_name=u'供应商')
    ware_house = models.IntegerField(default=constants.WARE_NONE,choices=constants.WARE_CHOICES
                                      ,db_index=True,verbose_name=u'所属仓库')

    express_code = models.CharField(max_length=32, verbose_name=u'预填快递公司')
    express_no = models.CharField(max_length=32, db_index=True, verbose_name=u'预填运单号')

    creator = models.CharField(max_length=30, db_index=True, verbose_name=u'入仓员')
    inspector = models.CharField(max_length=30, db_index=True, verbose_name=u'检货员')

    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')

    status = models.CharField(max_length=30,
                              default=STAGING,
                              db_index=True,
                              choices=STATUS_CHOICES,
                              verbose_name=u'状态')

    def __unicode__(self):
        return str(self.id)

    class Meta:
        db_table = 'forecast_real_inbound'
        app_label = 'forecast'
        verbose_name = u'V2入仓单'
        verbose_name_plural = u'V2入仓单列表'

    def __unicode__(self):
        return '<%s, %s, %s>' % (self.id, self.wave_no, self.supplier and self.supplier.supplier_name or u'未知供应商')

    @property
    def status_name(self):
        return self.get_status_display()

    @property
    def normal_details(self):
        return self.inbound_detail_manager.filter(status=RealInboundDetail.NORMAL)

    @property
    def total_detail_num(self):
        return self.total_inbound_num


class RealInboundDetail(BaseModel):

    NORMAL   = 'normal'
    INVALID  = 'invalid'
    STATUS_CHOICES = (
        (NORMAL, u'有效'),
        (INVALID, u'作废'),
    )

    inbound = models.ForeignKey(RealInbound,
                                related_name='inbound_detail_manager',
                                verbose_name=u'入仓单')

    product_id = models.IntegerField(db_index=True, verbose_name=u'商品ID')
    sku_id = models.IntegerField(null=False, verbose_name=u'规格ID')

    barcode = models.CharField(max_length=64, blank=True, verbose_name=u'商品条码')
    product_name = models.CharField(max_length=128, blank=True, verbose_name=u'商品全称')
    product_img  = models.CharField(max_length=256, blank=True, verbose_name=u'商品图片')
    arrival_quantity = models.IntegerField(default=0, verbose_name=u'已到数量')
    inferior_quantity = models.IntegerField(default=0, verbose_name=u'次品数量')

    district = models.CharField(max_length=64, blank=True, verbose_name=u'库位')
    status   = models.CharField(max_length=8, choices=STATUS_CHOICES, default=NORMAL, verbose_name=u'状态')

    def __unicode__(self):
        return str(self.id)

    class Meta:
        db_table = 'forecast_real_inbounddetail'
        unique_together = ['sku_id', 'inbound']
        app_label = 'forecast'
        verbose_name = u'V2入仓单明细'
        verbose_name_plural = u'V2入仓单明细列表'

    def __unicode__(self):
        return '<%s, %s, %s>' % (self.id, self.product_name, self.arrival_quantity)


# def update_realinbound_data(sender, instance, created, **kwargs):
#     real_inbound = instance.inbound
#
#     real_inbound.total_inbound_num = \
#         sum(real_inbound.normal_details.values_list('arrival_quantity',flat=True))
#     real_inbound.total_inferior_num = \
#         sum(real_inbound.normal_details.values_list('inferior_quantity', flat=True))
#     real_inbound.save(update_fields=['total_inbound_num', 'total_inferior_num'])
#
#     forecast_inbound = real_inbound.forecast_inbound
#     real_inbounds = RealInbound.objects.filter(forecast_inbound=forecast_inbound)
#     forecast_inbound_details = RealInboundDetail.objects.filter(
#         inbound__in=real_inbounds, status=RealInboundDetail.NORMAL
#     )
#     if forecast_inbound:
#         forecast_inbound.total_arrival_num = \
#             sum(forecast_inbound_details.values_list('arrival_quantity', flat=True))
#         forecast_inbound.save(update_fields=['total_arrival_num'])
#
#
# post_save.connect(
#     update_realinbound_data,
#     sender=RealInboundDetail,
#     dispatch_uid='post_save_update_realinbound_data')

