# coding=utf-8
from django.db import models
from core.models import BaseModel
from statistics.managers import StatisticSaleNumManager


class StatisticSaleNum(BaseModel):
    TYPE_SKU = 1
    TYPE_COLOR = 4
    TYPE_MODEL = 7
    TYPE_CATEGORY = 10
    TYPE_SUPPLIER = 13
    TYPE_TOTAL = 16

    RECORD_CHOICE = (
        (TYPE_SKU, u'SKU级'),
        (TYPE_COLOR, u'颜色级'),
        (TYPE_MODEL, u'款式级'),
        (TYPE_CATEGORY, u'类别级'),
        (TYPE_SUPPLIER, u'供应商级'),
        (TYPE_TOTAL, u'总计级'),
    )
    # upper_grade  target_id 总计的记录中是为空的

    upper_grade = models.BigIntegerField(blank=True, null=True, db_index=True, verbose_name=u'上一级id')
    target_id = models.BigIntegerField(db_index=True, blank=True, null=True, verbose_name=u'级别对应instance_id')
    pay_date = models.DateField(db_index=True, verbose_name=u'付款日期')
    uniq_id = models.CharField(db_index=True, max_length=32, verbose_name=u'唯一标识')
    record_type = models.IntegerField(choices=RECORD_CHOICE, db_index=True, verbose_name=u'记录类型')
    sale_num = models.IntegerField(default=0, verbose_name=u'销售数量')
    sale_value = models.FloatField(default=0, verbose_name=u'销售金额')
    stock_out_num = models.IntegerField(default=0, verbose_name=u'缺货数量')
    before_post_ref_num = models.IntegerField(default=0, verbose_name=u'发货前退货数量')
    after_post_ref_num = models.IntegerField(default=0, verbose_name=u'发货后退货数量')
    objects = StatisticSaleNumManager()

    def __unicode__(self):
        return u'<%s-%s>' % (self.id, self.target_id)
