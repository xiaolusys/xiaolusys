# coding:utf-8
import datetime

from django.db import models
from django.db.models.signals import post_save

from core.models import BaseModel
from supplychain.supplier.models import SaleSupplier
from shopback.items.models import Product, ProductSku

from . import constants

def default_forecast_inbound_no(identify_id=None):
    identify_id  = identify_id or str(datetime.datetime.now().time().microsecond)
    return 'FI'+datetime.datetime.now().strftime('%Y%m%d') + '-' + identify_id

class ForecastInbound(BaseModel):
    ST_DRAFT = 'draft'
    ST_APPROVED = 'approved'
    ST_ARRIVED = 'arrived'
    ST_CANCELED = 'canceled'

    STATUS_CHOICES = (
        (ST_DRAFT, u'草稿'),
        (ST_APPROVED, u'审核'),
        (ST_ARRIVED, u'到货'),
        (ST_CANCELED, u'取消'),
    )

    forecast_no = models.CharField(max_length=32, default=default_forecast_inbound_no,
                                   unique=True, verbose_name=u'入库批次')

    supplier = models.ForeignKey(SaleSupplier,
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

    purchaser = models.CharField(max_length=30, blank=True, db_index=True, verbose_name=u'采购员')

    status = models.CharField(max_length=8, db_index=True, default=ST_DRAFT, choices=STATUS_CHOICES, verbose_name=u'状态')

    is_lackordefect = models.BooleanField(default=False,db_index=True,verbose_name=u'缺货或次品')
    is_overorwrong  = models.BooleanField(default=False,db_index=True,verbose_name=u'多到或错货')

    class Meta:
        db_table = 'forecast_inbound'
        app_label = 'forecast'
        verbose_name = u'预测到货单'
        verbose_name_plural = u'预测到货单列表'

    def __unicode__(self):
        return '<%s,%s>' %(self.id, self.supplier.supplier_name)

    @property
    def status_name(self):
        return self.get_status_display()

    @property
    def total_detail_num(self):
        forecast_nums = self.normal_details().values_list('forecast_arrive_num', flat=True)
        return forecast_nums and sum(forecast_nums) or 0

    def get_ware_house_name(self):
        return dict(constants.WARE_CHOICES).get(self.ware_house)


    def normal_details(self):
        return self.details_manager.filter(status=ForecastInboundDetail.NORMAL)

    def is_unrecord_logistic(self):
        return self.express_code == '' or self.express_no == ''

    def inbound_arrive_update_status(self):
        self.status = self.ST_ARRIVED
        self.save()



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


def default_inbound_ware_no():
    return datetime.datetime.now().strftime('%Y%m%d') + '-1'

def uniq_staging_inbound_record(supplier_id, ware_house, creator, sku_id):
    staging_ibs = StagingInBound.objects.filter(supplier_id=supplier_id,
                                  ware_house=ware_house,
                                  creator=creator,
                                  sku_id=sku_id,
                                  status=StagingInBound.COMPLETED)
    staging_count = staging_ibs.count()
    return '%s-%s-%s-%s-%s'%(supplier_id, ware_house, creator, sku_id, staging_count)


class StagingInBound(BaseModel):

    STAGING = 'staging'
    COMPLETED = 'completed'
    CANCELED = 'canceled'

    STATUS_CHOICES = ((STAGING, u'待入库'), (COMPLETED, u'已入库'),(CANCELED, u'已取消'))

    forecast_inbound = models.ForeignKey(ForecastInbound, null=True, related_name='staging_records', verbose_name=u'关联预测单')
    wave_no = models.CharField(max_length=32, default=default_inbound_ware_no, db_index=True, verbose_name=u'入库批次')
    supplier = models.ForeignKey(SaleSupplier, null=True, related_name='staging_inbound_manager', verbose_name=u'供应商')
    ware_house = models.IntegerField(default=constants.WARE_NONE,choices=constants.WARE_CHOICES
                                      ,db_index=True,verbose_name=u'所属仓库')

    product_id = models.IntegerField(default=0, db_index=True, verbose_name=u'商品ID')
    sku_id = models.IntegerField(default=0, db_index=True, verbose_name=u'规格ID')
    record_num = models.IntegerField(default=0, verbose_name=u'录入数量')

    uniq_key = models.CharField(max_length=64, unique=True)
    creator = models.CharField(max_length=30, db_index=True, verbose_name=u'操作员')
    status = models.CharField(max_length=16,
                              default=STAGING,
                              db_index=True,
                              choices=STATUS_CHOICES,
                              verbose_name=u'状态')

    def __unicode__(self):
        return str(self.id)

    class Meta:
        db_table = 'forcast_staging_inbound_record'
        app_label = 'forecast'
        verbose_name = u'到货预录单'
        verbose_name_plural = u'到货预录单列表'

    def __unicode__(self):
        return '<%s, %s, %s>' % (self.id, self.wave_no, self.supplier.supplier_name)

    def get_ware_house_name(self):
        return dict(constants.WARE_CHOICES).get(self.ware_house)

    def get_product(self):
        product_sku = ProductSku.objects.filter(id=self.sku_id).first()
        if not product_sku:
            return {}
        product = product_sku.product
        return {
            'product_id': product.id,
            'sku_id': product_sku.id,
            'product_name': '%s - %s'%(product.name, product_sku.name),
            'product_img': product.PIC_PATH,
            'barcode':product_sku.barcode
        }

    product = property(get_product)

class RealInBound(BaseModel):

    STAGING = 'staging'
    COMPLETED = 'completed'
    CANCELED = 'canceled'

    STATUS_CHOICES = ((STAGING, u'待入库'), (COMPLETED, u'已入库'),(CANCELED, u'已取消'))

    wave_no = models.CharField(max_length=32, default=default_inbound_ware_no, db_index=True, verbose_name=u'入库批次')

    forecast_inbound = models.ForeignKey(ForecastInbound,  related_name='real_inbound_manager',
                                         null=True, verbose_name=u'关联预测到货单')
    relate_order_set = models.ManyToManyField('dinghuo.OrderList', related_name='real_inbounds',
                                         verbose_name=u'关联订货单')

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
        return '<%s, %s, %s>' % (self.id, self.wave_no, self.supplier.supplier_name)

    @property
    def status_name(self):
        return self.get_status_display()

    def normal_details(self):
        return self.inbound_detail_manager.filter(status=RealInBoundDetail.NORMAL)

    @property
    def total_detail_num(self):
        arrive_nums = self.normal_details().values_list('arrival_quantity', flat=True)
        return arrive_nums and sum(arrive_nums) or 0

class RealInBoundDetail(BaseModel):

    NORMAL   = 'normal'
    INVALID  = 'invalid'
    STATUS_CHOICES = (
        (NORMAL, u'有效'),
        (INVALID, u'作废'),
    )

    inbound = models.ForeignKey(RealInBound,
                                related_name='inbound_detail_manager',
                                verbose_name=u'入仓单')

    product_id = models.IntegerField(verbose_name=u'商品ID')
    sku_id = models.IntegerField(verbose_name=u'规格ID')

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
        db_table = 'forcast_real_inbounddetail'
        app_label = 'forecast'
        verbose_name = u'V2入仓单明细'
        verbose_name_plural = u'V2入仓单明细列表'

    def __unicode__(self):
        return '<%s, %s, %s>' % (self.id, self.product_name, self.arrival_quantity)
