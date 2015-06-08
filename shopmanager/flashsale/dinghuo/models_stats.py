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
        verbose_name = u'每日组别统计'
        verbose_name_plural = u'每日组别统计'

    def __unicode__(self):
        return '<%s,%s,%s>' % (self.id, self.group, self.stats_time)


class SupplyChainStatsOrder(models.Model):
    product_id = models.CharField(max_length=32, verbose_name=u'商品id')
    outer_sku_id = models.CharField(max_length=32, verbose_name=u'规格外部id')
    sale_time = models.DateField(verbose_name=u'统计时间')
    ding_huo_num = models.IntegerField(default=0, verbose_name=u'订货数量')
    sale_num = models.IntegerField(default=0, verbose_name=u'销售数量')
    arrival_num = models.IntegerField(default=0, verbose_name=u'到货数量')
    goods_out_num = models.IntegerField(default=0, verbose_name=u'发出数量')
    trade_general_time = models.BigIntegerField(default=0, verbose_name=u'下单时间')
    order_deal_time = models.BigIntegerField(default=0, verbose_name=u'订货时间')
    goods_arrival_time = models.BigIntegerField(default=0, verbose_name=u'到货时间')
    goods_out_time = models.BigIntegerField(default=0, verbose_name=u'到货发出时间')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        db_table = 'supply_chain_stats_order'
        unique_together = ('product_id', 'outer_sku_id', 'sale_time')
        verbose_name = u'供应链数据统计表'
        verbose_name_plural = u'供应链数据统计表'

    def __unicode__(self):
        return '<%s,%s,%s>' % (self.product_id, self.outer_sku_id, self.sale_time)
