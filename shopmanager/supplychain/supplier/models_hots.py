# coding=utf-8
"""
爆款表
"""
from django.db import models
from shopback.base.fields import BigIntegerForeignKey
from django.contrib.auth.models import User


class HotProduct(models.Model):
    SELECTED = 0
    PASSED = 1
    MANUFACTURE = 2
    SALE = 3
    CLOSE = 4
    CANCEL = 5
    STATUS_CHOICES = ((SELECTED, u'入围'),
                      (PASSED, u'待生产'),
                      (MANUFACTURE, u'生产'),
                      (SALE, u'开卖'),
                      (CLOSE, u'结束'),  # 全状态结束
                      (CANCEL, u'作废'))  # 中断

    name = models.CharField(max_length=128, verbose_name=u'名称')
    pic_pth = models.CharField(max_length=512, verbose_name=u'图片链接')
    site_url = models.CharField(max_length=512, verbose_name=u'站点链接')
    price = models.FloatField(default=0.0, verbose_name=u'预售价格')
    hot_value = models.IntegerField(default=0, verbose_name=u'热度值')
    voting = models.BooleanField(default=False, verbose_name=u'参与投票')
    memo = models.TextField(max_length=1024, blank=True, verbose_name=u'备注')
    status = models.IntegerField(default=0, choices=STATUS_CHOICES, verbose_name=u'爆款状态')
    contactor = BigIntegerForeignKey(User, null=True, related_name='hot_products', verbose_name=u'接洽人')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'supplychain_hot_product'
        verbose_name = u'特卖/爆款表'
        verbose_name_plural = u'特卖/爆款列表'

    def __unicode__(self):
        return self.name