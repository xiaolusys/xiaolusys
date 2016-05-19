# coding=utf-8
from django.db import models
from core.models import BaseModel
from django.db.models.signals import post_save


class SaleOrderStatsRecord(BaseModel):
    NOT_PAY = 0
    PAID = 1
    CANCEL = 2
    OUT_STOCK = 3
    RETURN_GOODS = 4

    STATUS = (
        (NOT_PAY, u'未付款'),
        (PAID, u'已付款'),
        (CANCEL, u'发货前退款'),
        (OUT_STOCK, u'缺货退款'),
        (RETURN_GOODS, u'退货退款'),
    )

    HAS_RETURN = 1
    NO_RETURN = 0
    RETURN_CHOICES = (
        (HAS_RETURN, u'有申请退货'),
        (NO_RETURN, u'无申请退货'),
    )

    oid = models.CharField(max_length=40, unique=True, verbose_name=u'sale_order_oid')
    outer_id = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'外部编码')
    sku_id = models.CharField(max_length=32, blank=True, verbose_name=u'规格外部编码')  # 实际保存的是 outer_id + '/'+outer_sku_id
    name = models.CharField(max_length=64, verbose_name=u'商品SKU描述')  # title + sku_name
    pic_path = models.CharField(max_length=256, verbose_name=u'图片')
    num = models.IntegerField(default=0, verbose_name=u'数量')
    payment = models.FloatField(default=0, verbose_name=u'实付款')
    pay_time = models.DateTimeField(db_index=True, blank=True, null=True, verbose_name=u'付款时间')
    date_field = models.DateField(db_index=True, null=True, blank=True, verbose_name=u'日期')
    status = models.IntegerField(choices=STATUS, db_index=True, verbose_name=u'状态')
    return_goods = models.IntegerField(default=NO_RETURN, choices=RETURN_CHOICES, verbose_name=u'退货标记')

    class Meta:
        db_table = 'statistics_sale_order_stats_record'
        app_label = 'statistics'
        verbose_name = '交易统计明细'
        verbose_name_plural = '交易统计明细列表'


def update_salestats(sender, instance, created, **kwargs):
    from statistics.tasks import task_statsrecord_update_salestats
    task_statsrecord_update_salestats.delay(instance)


post_save.connect(update_salestats, sender=SaleOrderStatsRecord, dispatch_uid='post_save_update_salestats')


class SaleStats(BaseModel):
    TYPE_SKU = 1
    TYPE_COLOR = 4
    TYPE_MODEL = 7
    TYPE_SUPPLIER = 13
    TYPE_BD = 14
    TYPE_TOTAL = 16

    RECORD_TYPES = (
        (TYPE_SKU, u'SKU级'),
        (TYPE_COLOR, u'颜色级'),
        (TYPE_MODEL, u'款式级'),
        (TYPE_SUPPLIER, u'供应商级'),
        (TYPE_BD, u'买手BD级'),
        (TYPE_TOTAL, u'总计级'),
    )

    NOT_PAY = 0
    PAID = 1
    CANCEL = 2
    OUT_STOCK = 3
    RETURN_GOODS = 4

    STATUS = (
        (NOT_PAY, u'未付款'),
        (PAID, u'已付款'),
        (CANCEL, u'发货前退款'),
        (OUT_STOCK, u'缺货退款'),
        (RETURN_GOODS, u'退货退款'),
    )

    parent_id = models.CharField(max_length=32, db_index=True, blank=True, null=True, verbose_name=u'上一级id')
    current_id = models.CharField(max_length=32, db_index=True, blank=True, null=True, verbose_name=u'级别对应instance_id')
    date_field = models.DateField(db_index=True, verbose_name=u'付款日期')
    name = models.CharField(max_length=64, null=True, verbose_name=u'商品描述')  # title + sku_name
    pic_path = models.CharField(max_length=256, null=True, verbose_name=u'图片')
    num = models.IntegerField(default=0, verbose_name=u'销售数量')
    payment = models.FloatField(default=0, verbose_name=u'销售金额')
    uni_key = models.CharField(max_length=64, unique=True, verbose_name=u'唯一标识')
    record_type = models.IntegerField(choices=RECORD_TYPES, db_index=True, verbose_name=u'记录类型')
    status = models.IntegerField(choices=STATUS, db_index=True, verbose_name=u'状态')

    # uni_key = date_field + current_id + record_type + status
    def __unicode__(self):
        return u'<%s-%s>' % (self.id, self.uni_key)

    class Meta:
        db_table = 'statistics_sale_stats'
        app_label = 'statistics'
        verbose_name = u'销量统计表'
        verbose_name_plural = u'销量统计列表'


def update_parent_sale_stats(sender, instance, created, **kwargs):
    if instance.record_type >= SaleStats.TYPE_TOTAL:  # 总计级别的变化不去触发信号
        return
    from statistics.tasks import task_update_parent_sale_stats
    task_update_parent_sale_stats.delay(instance)


post_save.connect(update_parent_sale_stats, sender=SaleStats, dispatch_uid='post_save_update_parent_sale_stats')
