# -*- coding:utf-8 -*-
__author__ = 'yann'
from django.db import models


class SupplyChainDataStats(models.Model):
    sale_quantity = models.IntegerField(default=0, verbose_name=u'销售数量')
    cost_amount = models.FloatField(default=0, verbose_name=u'成本额')
    turnover = models.FloatField(default=0, verbose_name=u'销售额')
    order_goods_quantity = models.FloatField(default=0, verbose_name=u'订货数量')
    order_goods_amount = models.FloatField(default=0, verbose_name=u'订货总价')
    stats_time = models.DateField(verbose_name=u'统计时间')
    group = models.CharField(max_length=8, verbose_name=u'组别')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        db_table = 'supply_chain_data_stats'
        unique_together = ('stats_time', 'group')
        verbose_name = u'供应链数据统计表'
        verbose_name_plural = u'供应链数据统计表'