# coding=utf-8

from django.db import models
from core.models import BaseModel

class SupplierFigure(BaseModel):
    supplier = models.OneToOneField('supplier.SaleSupplier', related_name='figures', unique=True, verbose_name=u'供应商')
    schedule_num = models.IntegerField(default=0, verbose_name=u'选款数量')

    no_pay_num = models.IntegerField(default=0, verbose_name=u'未付款数量')
    pay_num = models.IntegerField(default=0, verbose_name=u'付款数量')
    cancel_num = models.IntegerField(default=0, verbose_name=u'发货前退款数量')
    out_stock_num = models.IntegerField(default=0, verbose_name=u'缺货退款数量')
    return_good_num = models.IntegerField(default=0, verbose_name=u'退货退款数量')

    return_good_rate = models.FloatField(default=0.0, db_index=True, verbose_name=u'退货率')
    # 退货率 = return_good_num/return_good_num+pay_num

    payment = models.FloatField(default=0.0, verbose_name=u'销售金额')
    cancel_amount = models.FloatField(default=0.0, verbose_name=u'发货前退款金额')
    out_stock_amount = models.FloatField(default=0.0, verbose_name=u'缺货退款金额')
    return_good_amount = models.FloatField(default=0.0, verbose_name=u'退货退款金额')

    avg_post_days = models.FloatField(default=0.0, verbose_name=u'平均发货天数')

    class Meta:
        db_table = 'supplychain_supply_supplier_figure'
        app_label = 'supplier'
        verbose_name = u'供应商/数据表'
        verbose_name_plural = u'供应商/数据列表'

    def __unicode__(self):
        return "%s-%s" % (self.id, self.supplier.supplier_name)
