# coding:utf-8
import datetime
import random
from django.db import models
from django.db.models.signals import post_save

from core.models import BaseModel
from core.utils.unikey import uniqid

from .. import constants

def default_forecast_inbound_no(identify_id = None):
    identify_id  = identify_id or uniqid()
    return 'FI'+datetime.datetime.now().strftime('%Y%m%d') + '-' + identify_id

class ForecastInbound(BaseModel):
    ST_DRAFT = 'draft'
    ST_APPROVED = 'approved'
    ST_ARRIVED = 'arrived'
    ST_TIMEOUT = 'timeout'
    ST_CLOSE   = 'close'
    ST_CANCELED = 'canceled'

    STATUS_CHOICES = (
        (ST_DRAFT, u'草稿'),
        (ST_APPROVED, u'审核'),
        (ST_ARRIVED, u'到货'),
        (ST_TIMEOUT, u'超时关闭'),
        (ST_CLOSE, u'缺货关闭'),
        (ST_CANCELED, u'取消'),
    )

    forecast_no = models.CharField(max_length=32,  default=default_forecast_inbound_no,
                                   db_index=True, verbose_name=u'入库批次')
    supplier = models.ForeignKey('supplier.SaleSupplier',
                                 null=True,
                                 blank=True,
                                 related_name='forecast_inbound_manager',
                                 verbose_name=u'供应商')

    relate_order_set = models.ManyToManyField('dinghuo.OrderList',
                                              related_name='forecase_inbounds', verbose_name=u'关联订货单')
    ware_house = models.IntegerField(default=constants.WARE_NONE,
                                      choices=constants.WARE_CHOICES,verbose_name=u'所属仓库')

    express_code = models.CharField(max_length=32, blank=True, verbose_name=u'预填快递公司')
    express_no = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'预填运单号')
    forecast_arrive_time = models.DateTimeField(blank=True, null=True, verbose_name=u'预测到货时间')

    total_forecast_num = models.IntegerField(default=0, verbose_name=u'总预测数')
    total_arrival_num = models.IntegerField(default=0, verbose_name=u'总到货数')

    purchaser = models.CharField(max_length=30, blank=True, db_index=True, verbose_name=u'采购员')

    status = models.CharField(max_length=8, db_index=True, default=ST_DRAFT,
                              choices=STATUS_CHOICES, verbose_name=u'状态')
    memo = models.TextField(max_length=1000, blank=True, verbose_name=u'备注')

    delivery_time = models.DateTimeField(blank=True, null=True, db_index=True,verbose_name=u'发货时间')
    arrival_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'到货时间')

    is_unrecordlogistic = models.BooleanField(default=False, verbose_name=u'未及时催货')
    has_lack = models.BooleanField(default=False,db_index=True,verbose_name=u'缺货')
    has_defact  = models.BooleanField(default=False,db_index=True,verbose_name=u'次品')
    has_overhead = models.BooleanField(default=False,db_index=True,verbose_name=u'多到')
    has_wrong = models.BooleanField(default=False,db_index=True,verbose_name=u'错发')

    class Meta:
        db_table = 'forecast_inbound'
        app_label = 'forecast'
        verbose_name = u'预测到货单'
        verbose_name_plural = u'预测到货单列表'

    def __unicode__(self):
        return '<%s,%s>' %(self.id, self.supplier and self.supplier.supplier_name or u'未知供应商')

    @property
    def status_name(self):
        return self.get_status_display()

    @property
    def total_detail_num(self):
        forecast_nums = self.normal_details.values_list('forecast_arrive_num', flat=True)
        return forecast_nums and sum(forecast_nums) or 0

    @property
    def real_arrive_num(self):
        from .inbound import RealInBound, RealInBoundDetail
        relate_inbounds = RealInBound.objects.filter(forecast_inbound=self)
        arrival_quantitys = RealInBoundDetail.objects.filter(inbound__in=relate_inbounds,
                                                             status=RealInBoundDetail.NORMAL)\
                                                            .values_list('arrival_quantity', flat=True)
        return arrival_quantitys and sum(arrival_quantitys) or 0

    def get_ware_house_name(self):
        return dict(constants.WARE_CHOICES).get(self.ware_house)

    @property
    def normal_details(self):
        return self.details_manager.filter(status=ForecastInboundDetail.NORMAL)

    def is_unrecord_logistic(self):
        return self.express_code == '' or self.express_no == ''

    def is_inthedelivery(self):
        """ 是否发货中 """
        return self.status in (self.ST_DRAFT, self.ST_APPROVED)

    def is_arrival_except(self):
        """ 是否到货异常 """
        return self.has_lack or self.has_defact or self.has_overhead or self.has_wrong

    def is_arrival_timeout(self):
        """ 到货超时 """
        tnow = datetime.datetime.now()
        if self.status == self.ST_APPROVED and \
            (not self.forecast_arrive_time or self.forecast_arrive_time < tnow):
            return True
        if self.status == self.ST_TIMEOUT:
            return True
        return False

    def inbound_arrive_update_status(self, arrival_time=None):
        if self.is_unrecord_logistic():
            self.is_unrecordlogistic = True
        if not self.arrival_time:
            self.arrival_time = arrival_time or datetime.datetime.now()
        self.status = self.ST_ARRIVED


    def unarrive_close_update_status(self):
        self.status = self.ST_CANCELED

    def lackgood_close_update_status(self):
        self.status = self.ST_CLOSE


def modify_forecastinbound_data(sender, instance, created, **kwargs):

    if instance.express_no and not instance.delivery_time:
        instance.delivery_time = datetime.datetime.now()
        instance.save(update_fields=['delivery_time'])

    # refresh forecast stats
    from .. import tasks
    tasks.task_forecast_update_stats_data.delay(instance.id)

post_save.connect(
    modify_forecastinbound_data,
    sender=ForecastInbound,
    dispatch_uid='post_save_modify_forecastinbound_data')


class ForecastInboundDetail(BaseModel):

    NORMAL = 0
    DELETE = 1

    STATUS_CHOICES = (
        (NORMAL, u'普通'),
        (DELETE, u'删除'),
    )

    forecast_inbound = models.ForeignKey(ForecastInbound, related_name='details_manager', verbose_name=u'关联预测单')

    product_id = models.IntegerField(verbose_name=u'商品ID')
    sku_id = models.IntegerField(verbose_name=u'规格ID')
    forecast_arrive_num = models.IntegerField(verbose_name='预测到货数量')

    product_name = models.CharField(max_length=128, blank=True, verbose_name=u'商品全称')
    product_img = models.CharField(max_length=256, blank=True, verbose_name=u'商品图片')

    status = models.IntegerField(default=NORMAL, db_index=True, choices=STATUS_CHOICES, verbose_name=u'状态')

    class Meta:
        db_table = 'forecast_inbound_detail'
        app_label = 'forecast'
        verbose_name = u'预测到货明细'
        verbose_name_plural = u'预测到货明细列表'

    def __unicode__(self):
        return '<%s,%s,%s>' % (self.id, self.product_name, self.forecast_arrive_num)

    def get_productsku(self):
        if not hasattr(self, '__productsku__'):
            from shopback.items.models import ProductSku
            product_sku = ProductSku.objects.filter(id=self.sku_id).first()
            self.__productsku__ = product_sku
        return self.__productsku__

    product_sku = property(get_productsku)

    def get_product(self):
        product_sku = self.get_productsku()
        if product_sku:
            return product_sku.product
        return None

    product = property(get_product)

    @property
    def product_pic(self):
        return self.product.pic_path + '?imageMogr2/strip/format/jpg/quality/90/interlace/1/thumbnail/80/'


def update_forecastinbound_data(sender, instance, created, **kwargs):
    forecast_inbound = instance.forecast_inbound

    forecast_num = sum(forecast_inbound.normal_details.values_list('forecast_arrive_num',flat=True))
    forecast_inbound.total_forecast_num = forecast_num
    forecast_inbound.save(update_fields=['total_forecast_num'])

post_save.connect(
    update_forecastinbound_data,
    sender=ForecastInboundDetail,
    dispatch_uid='post_save_update_forecastinbound_data')
