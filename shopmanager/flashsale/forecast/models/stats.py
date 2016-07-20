# coding:utf-8
from django.db import models
from django.db.models.signals import post_save

from core.models import BaseModel

from .. import constants

class ForecastStats(BaseModel):

    STAGING = 'staging'
    ARRIVAL = 'arrival'
    EXCEPT  = 'except'
    CLOSED  = 'closed'
    STATUS_CHOICES = (
        (STAGING, u'待收货'),
        (ARRIVAL, u'已到货'),
        (EXCEPT, u'异常关闭'),
        (CLOSED, u'取消'),
    )

    forecast_inbound = models.OneToOneField('forecast.ForecastInbound', verbose_name=u'预测单')
    supplier = models.ForeignKey('supplier.SaleSupplier', verbose_name=u'供应商')
    buyer_name = models.CharField(max_length=32, db_index=True,verbose_name=u'买手名称')
    purchaser = models.CharField(max_length=32, db_index=True, verbose_name=u'采购员名称')

    purchase_num  = models.IntegerField(default=0, verbose_name=u'订货数量')
    inferior_num = models.IntegerField(default=0, verbose_name=u'次品数量')
    lack_num  = models.IntegerField(default=0, verbose_name=u'缺货数量')
    purchase_amount = models.IntegerField(default=0, verbose_name=u'订货金额')

    purchase_time = models.DateTimeField(null=True, db_index=True, blank=True,verbose_name=u'订货时间')
    delivery_time = models.DateTimeField(null=True, db_index=True, blank=True,verbose_name=u'发货时间')
    arrival_time  = models.DateTimeField(null=True, db_index=True, blank=True,verbose_name=u'到货时间')
    billing_time  = models.DateTimeField(null=True, blank=True,verbose_name=u'结算时间')
    finished_time = models.DateTimeField(null=True, blank=True, verbose_name=u'完成时间')

    has_lack = models.BooleanField(default=False, verbose_name=u'到货缺货')
    has_defact = models.BooleanField(default=False, verbose_name=u'次品')
    has_overhead = models.BooleanField(default=False, verbose_name=u'多到')
    has_wrong = models.BooleanField(default=False, verbose_name=u'错发')

    is_unrecordlogistic = models.BooleanField(default=False, verbose_name=u'未及时催货')
    is_timeout = models.BooleanField(default=False, verbose_name=u'预测超时')
    is_lackclose = models.BooleanField(default=False, verbose_name=u'下单缺货')

    status = models.CharField(max_length=16,default=STAGING,choices=STATUS_CHOICES,db_index=True,verbose_name=u'状态')
    def __unicode__(self):
        return str(self.id)

    class Meta:
        db_table = 'forecast_stats'
        app_label = 'forecast'
        verbose_name = u'预测单统计'
        verbose_name_plural = u'预测单统计列表'

    def __unicode__(self):
        return '<%s, %s>' % (self.id, self.supplier and self.supplier.supplier_name or u'未知供应商')

