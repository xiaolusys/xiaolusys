# coding=utf-8
from django.db import models


class SalePraise(models.Model):
    SALE_PRODUCT = 0
    Hot_Product = 1
    FROM_CHOICES = ((SALE_PRODUCT, u'特卖选品'),
                    (Hot_Product, u'爆款产品'))

    sale_id = models.BigIntegerField(db_index=True, verbose_name=u"选品ID")
    pro_from = models.IntegerField(default=0, choices=FROM_CHOICES, verbose_name=u'产品来源选择')
    cus_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u"客户ID")
    praise = models.BooleanField(default=False, verbose_name=u"是否点赞")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')

    class Meta:
        db_table = 'supplier_sale_product_praise'
        app_label = 'supplier'
        verbose_name = u'特卖/选品投票表'
        verbose_name_plural = u'特卖/选品投票列表'
        unique_together = ("sale_id", "cus_id", 'pro_from')

    def __unicode__(self):
        return u"{0}".format(self.sale_id)