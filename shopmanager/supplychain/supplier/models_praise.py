# coding=utf-8
from django.db import models


class SalePraise(models.Model):
    sale_id = models.BigIntegerField(verbose_name=u"选品ID")
    cus_id = models.BigIntegerField(default=0, verbose_name=u"客户ID")
    praise = models.BooleanField(default=False, verbose_name=u"是否点赞")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')

    class Meta:
        db_table = 'supplier_sale_product_praise'
        verbose_name = u'特卖/选品投票表'
        verbose_name_plural = u'特卖/选品投票列表'
        unique_together = ("sale_id", "cus_id")

    def __unicode__(self):
        return self.sale_id