# coding: utf-8
from __future__ import unicode_literals
from django.db import models

# Create your models here.
# 样品表
class SampleProduct(models.Model):
    WAIT_AUDIT = 0
    WAIT_DELIVERY = 1
    RECEIVER_CONFIRM = 2
    INVALID = 3

    STATUS_CHOICES = ((WAIT_AUDIT, U'已提交'),
                      (WAIT_DELIVERY, U'已审核'),
                      (RECEIVER_CONFIRM, U'已扫描'),
                      (INVALID, U'已作废'),)

    outer_id = models.CharField(max_length=16, db_index=True, blank=True, verbose_name=u'商品编码')
    title = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'商品名称')
    supplier = models.CharField(max_length=64, blank=True, verbose_name=u'供应商')

    pic_path = models.CharField(max_length=256, blank=True, verbose_name=u'图片链接')

    buyer = models.CharField(max_length=32, blank=True, default='', verbose_name=u'采购员')
    # 等于同一个商品编码下所有规格的总数
    num = models.IntegerField(default=0, verbose_name=u'样品总库存数量')

    payment = models.FloatField(default=0, verbose_name=u'付款金额')

    status = models.IntegerField(choices=STATUS_CHOICES, default=WAIT_AUDIT, verbose_name=u'样品状态')

    class Meta:
        db_table = 'sample_product'
        app_label = 'sampleproduct'
        verbose_name = u'样品'
        verbose_name_plural = u'样品信息表'

    def __unicode__(self):
        return self.title


# 样品规格表
class SampleProductSku(models.Model):
    NORMAL = 0
    DELETE = 1
    STATUS_CHOICES = ((NORMAL, u'正常'),
                      (DELETE, u'作废'),)

    outer_id = models.CharField(max_length=16, db_index=True, blank=True, verbose_name=u'规格编码')
    product = models.ForeignKey(SampleProduct, verbose_name=u'所属样品')

    sku_name = models.CharField(max_length=64, blank=True, verbose_name=u'规格尺寸')
    cost = models.FloatField(default=0, verbose_name=u'采购价格')
    payable = models.FloatField(default=0, verbose_name=u'应付金额')

    std_price = models.FloatField(default=0, verbose_name=u'吊牌价')
    num = models.IntegerField(default=0, verbose_name=u'规格库存数量')
    purchase_num = models.IntegerField(default=0, verbose_name=u'采购数量')
    storage_num = models.IntegerField(default=0, verbose_name=u'扫描数量')
    sell_num = models.IntegerField(default=0, verbose_name=u'出售数量')

    status = models.IntegerField(choices=STATUS_CHOICES, default=NORMAL, verbose_name=u'规格状态')

    class Meta:
        db_table = 'sample_product_sku'
        app_label = 'sampleproduct'
        verbose_name = u'样品规格'

    def __unicode__(self):
        return self.sku_name


# 扫描临时表
class ScanLinShi(models.Model):
    pid = models.IntegerField(db_index=True, verbose_name=u'商品ID')
    sku_id = models.IntegerField(db_index=True, verbose_name=u'规格ID')
    title = models.CharField(max_length=64, blank=True, verbose_name=u'商品名称')
    sku_name = models.CharField(max_length=64, blank=True, verbose_name=u'规格名称')

    # 条码等于商品编码与规格编码的组合
    bar_code = models.CharField(max_length=64, blank=True, verbose_name=u'扫描条码')

    scan_num = models.IntegerField(default=0, verbose_name=u'扫描数量')
    scan_type = models.IntegerField(verbose_name=u'扫描类型')

    status = models.IntegerField(default=0, verbose_name=u'处理状态')

    class Meta:
        db_table = 'scan_linshi'
        app_label = 'sampleproduct'
        verbose_name = u'临时表'
        verbose_name_plural = u'扫描临时表'

    def __unicode__(self):
        return self.bar_code


# 扫描（出）入库表
class SampleScan(models.Model):
    SCAN_IN = 'in'
    SCAN_OUT = 'out'

    SCAN_TYPE_CHOICES = ((SCAN_IN, U'扫描入库'),
                         (SCAN_OUT, U'扫描出库'),)

    SCRAPT = 0
    COMPLETE = 1
    DELETE = 2
    STATUS_CHOICES = ((SCRAPT, u'未确认'),
                      (COMPLETE, u'已确认'),
                      (DELETE, u'作废'),)

    pid = models.IntegerField(db_index=True, verbose_name=u'商品ID')
    sku_id = models.IntegerField(db_index=True, verbose_name=u'规格ID')
    title = models.CharField(max_length=64, blank=True, verbose_name=u'商品名称')
    sku_name = models.CharField(max_length=64, blank=True, verbose_name=u'规格名称')

    # 条码等于商品编码与规格编码的组合
    bar_code = models.CharField(max_length=64, blank=True, verbose_name=u'扫描条码')

    scan_num = models.IntegerField(default=0, verbose_name=u'扫描数量')
    scan_type = models.CharField(max_length=8, choices=SCAN_TYPE_CHOICES, verbose_name=u'扫描类型')
    created = models.DateField(u'扫描时间', auto_now_add=True, null=True, blank=True)

    status = models.IntegerField(choices=STATUS_CHOICES, default=SCRAPT, verbose_name=u'处理状态')

    class Meta:
        db_table = 'sample_scan'
        app_label = 'sampleproduct'
        verbose_name = u'（出）入库表'
        verbose_name_plural = u'样品（出）入库记录表'

    def __unicode__(self):
        return self.bar_code
