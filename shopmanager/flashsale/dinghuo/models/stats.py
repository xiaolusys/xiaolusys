# -*- coding:utf-8 -*-
from __future__ import division
__author__ = 'yann'
from django.db import models

from core.models import BaseModel

import logging
logger = logging.getLogger(__name__)


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
        app_label = 'dinghuo'
        verbose_name = u'每日组别统计'
        verbose_name_plural = u'每日组别统计'

    def __unicode__(self):
        return '<%s,%s,%s>' % (self.id, self.group, self.stats_time)


class SupplyChainStatsOrder(models.Model):
    product_id = models.CharField(max_length=32, verbose_name=u'商品id')
    outer_sku_id = models.CharField(max_length=32, verbose_name=u'规格外部id')
    sale_time = models.DateField(db_index=True, verbose_name=u'统计时间')
    shelve_time = models.DateField(verbose_name=u'上架时间')
    ding_huo_num = models.IntegerField(default=0, verbose_name=u'订货数量')
    sale_num = models.IntegerField(default=0, verbose_name=u'销售数量')
    arrival_num = models.IntegerField(default=0, verbose_name=u'到货数量')
    goods_out_num = models.IntegerField(default=0, verbose_name=u'发出数量')
    trade_general_time = models.BigIntegerField(default=0, verbose_name=u'下单时间')
    order_deal_time = models.BigIntegerField(default=0, verbose_name=u'订货时间')
    goods_arrival_time = models.BigIntegerField(default=0, verbose_name=u'到货时间')
    goods_out_time = models.BigIntegerField(default=0, verbose_name=u'到货发出时间')
    refund_amount_num = models.IntegerField(default=0, verbose_name=u"退款数量")
    refund_num = models.IntegerField(default=0, verbose_name=u"退货数量")
    created = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=u'创建日期')
    updated = models.DateTimeField(auto_now=True, db_index=True, verbose_name=u'更新日期')

    class Meta:
        db_table = 'supply_chain_stats_order'
        unique_together = ('product_id', 'outer_sku_id', 'sale_time')
        app_label = 'dinghuo'
        verbose_name = u'数据原始统计表'
        verbose_name_plural = u'数据原始统计表'

    def __unicode__(self):
        return '<%s,%s,%s>' % (self.product_id, self.outer_sku_id, self.sale_time)


class DailySupplyChainStatsOrder(models.Model):
    product_id = models.CharField(max_length=32, db_index=True, verbose_name=u'商品id')
    sale_time = models.DateField(db_index=True, verbose_name=u'上架时间')
    trade_general_time = models.BigIntegerField(default=0, verbose_name=u'下单时间')
    order_deal_time = models.BigIntegerField(default=0, verbose_name=u'订货时间')
    goods_arrival_time = models.BigIntegerField(default=0, verbose_name=u'到货时间')
    goods_out_time = models.BigIntegerField(default=0, verbose_name=u'到货发出时间')
    ding_huo_num = models.IntegerField(default=0, verbose_name=u'订货数量')
    sale_num = models.IntegerField(default=0, verbose_name=u'销售数量')
    fahuo_num = models.IntegerField(default=0, verbose_name=u'发货数量')
    cost_of_product = models.FloatField(default=0, verbose_name=u'成本')
    sale_cost_of_product = models.FloatField(default=0, verbose_name=u'销售额')
    return_num = models.IntegerField(default=0, verbose_name=u'退款数量')
    return_pro = models.IntegerField(default=0, verbose_name=u'退货数量')
    inferior_num = models.IntegerField(default=0, verbose_name=u'次品数量')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        db_table = 'supply_chain_stats_daily'
        unique_together = ('product_id', 'sale_time')
        app_label = 'dinghuo'
        verbose_name = u'供应链数据统计表'
        verbose_name_plural = u'供应链数据统计表'

    def __unicode__(self):
        return '<%s>' % (self.product_id)


class RecordGroupPoint(models.Model):
    ARRIVAL_POINT = '1'
    SALE_POINT = '2'
    POINT_TYPE_CHOICE = (
        (ARRIVAL_POINT, u'到货'),
        (SALE_POINT, u'销售'),
    )
    group_id = models.CharField(max_length=32, verbose_name=u'组')
    group_name = models.CharField(max_length=32, verbose_name=u'组名')
    point_type = models.CharField(max_length=32, verbose_name=u'加分类型', choices=POINT_TYPE_CHOICE)
    point_content = models.CharField(max_length=32, verbose_name=u'加分内容')
    get_point = models.IntegerField(default=0, verbose_name=u'分数')
    record_time = models.DateField(auto_now_add=True, verbose_name=u'奖励时间')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        db_table = 'record_group_point_detail'
        unique_together = ('point_type', 'point_content')
        app_label = 'dinghuo'
        verbose_name = u'积分表'
        verbose_name_plural = u'积分表'

    def __unicode__(self):
        return '<%s>' % (self.point_content)


class DailyStatsPreview(models.Model):
    sale_time = models.DateField(db_index=True, verbose_name=u'上架时间')
    shelf_num = models.IntegerField(default=0, verbose_name=u'日上架数量')
    sale_num = models.IntegerField(default=0, verbose_name=u'日销售数量')
    return_num = models.IntegerField(default=0, verbose_name=u'日退款数量')
    goods_out_time = models.BigIntegerField(default=0, verbose_name=u'日发货速度')
    cost_of_product = models.FloatField(default=0, verbose_name=u'日成本')
    sale_money = models.FloatField(default=0, verbose_name=u'日销售额')
    return_money = models.FloatField(default=0, verbose_name=u'日退款总额')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        db_table = 'supply_chain_daily_summary'
        unique_together = ('sale_time',)
        app_label = 'dinghuo'
        verbose_name = u'日汇'
        verbose_name_plural = u'供应链数据日汇表'

    def __unicode__(self):
        return '<%s>' % (self.sale_time)

    # @property
    # def time_to_day(self):
    #     time_of_long = self.goods_out_time
    #     days = 0
    #     tm_hours = 0
    #     if time_of_long > 0:
    #         days = time_of_long / 86400
    #         tm_hours = time_of_long % 86400 / 3600
    #     if days > 0 or tm_hours > 0:
    #         return str(days) + "天" + str(tm_hours) + "小时"
    #     else:
    #         return ""
    @property
    def time_to_day(self):
        time_of_long = self.goods_out_time
        days = 0
        if time_of_long > 0:
            days = round(time_of_long / 86400, 1)
        if days > 0:
            return str(days)
        else:
            return "0"


class PayToPackStats(models.Model):
    pay_date = models.DateField(db_index=True, unique=True, verbose_name=u'付款之日')
    packed_sku_num = models.IntegerField(default=0, verbose_name=u'已发货sku数')
    total_days = models.FloatField(default=0, verbose_name=u'总耗天数')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    updated = models.DateTimeField(auto_now=True, verbose_name=u'更新日期')

    class Meta:
        db_table = 'supply_chain_paytopack'
        app_label = 'dinghuo'
        verbose_name = u'发货速度日汇'
        verbose_name_plural = u'发货速度日汇表'

    def __unicode__(self):
        return '<%s>' % (self.pay_date)

    def avg_post_days(self):
        return round(self.total_days / self.packed_sku_num, 2)

    avg_post_days.allow_tags = True
    avg_post_days.short_description = u"平均发货日期"



class PackageBackOrderStats(BaseModel):

    day_date = models.DateField(blank=False, null=False, verbose_name=u'统计日期')
    purchaser = models.ForeignKey('auth.User', blank=True, null=True, verbose_name=u'采购员')

    three_backorder_num = models.IntegerField(default=0, verbose_name=u'3天未发货订单数')
    five_backorder_num = models.IntegerField(default=0, verbose_name=u'5天未发货订单数')
    fifteen_backorder_num = models.IntegerField(default=0, verbose_name=u'1５天未发货订单数')

    backorder_ids = models.TextField(default='', blank=True, verbose_name=u'3天未发货订单ID')
    class Meta:
        db_table = 'flashsale_dinghuo_backorderstats'
        unique_together = ['day_date', 'purchaser']
        app_label = 'dinghuo'
        verbose_name = u'延时发货订单统计'
        verbose_name_plural = u'延时发货订单统计列表'
