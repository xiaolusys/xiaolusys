# coding=utf-8
import datetime
import random
from django.db import models
from django.db.models.signals import post_save

from core.models import BaseModel
from core.utils.unikey import uniqid
from supplychain.supplier.models import SaleSupplier
from shopback.items.models import Product, ProductSku

from shopback.warehouse import constants

def default_inbound_ware_no():
    return datetime.datetime.now().strftime('%Y%m%d') + '-1'

def gen_uniq_staging_inbound_record_id(supplier_id, ware_house, creator, sku_id):
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

    forecast_inbound = models.ForeignKey('forecast.ForecastInbound', null=True, related_name='staging_records', verbose_name=u'关联预测单')
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
        return '<%s,%s,%s>'%(self.id, self.product_name, self.record_num)

    class Meta:
        db_table = 'forecast_staging_inbound_record'
        app_label = 'forecast'
        verbose_name = u'到货预录单'
        verbose_name_plural = u'到货预录单列表'

    def __unicode__(self):
        return '<%s, %s, %s>' % (self.id, self.wave_no, self.supplier.supplier_name)

    def get_ware_house_name(self):
        return dict(constants.WARE_CHOICES).get(self.ware_house)

    def get_product(self):
        if not hasattr(self, '_product_'):
            product_sku = ProductSku.objects.filter(id=self.sku_id).first()
            if not product_sku:
                return {}
            product = product_sku.product
            self._product_ = {
                'product_id': product.id,
                'sku_id': product_sku.id,
                'product_name': '%s - %s'%(product.name, product_sku.name),
                'product_img': product.PIC_PATH,
                'barcode':product_sku.barcode
            }
        return self._product_

    product = property(get_product)