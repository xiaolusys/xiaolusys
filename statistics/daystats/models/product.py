# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime

from django.db import models
from core.models import BaseModel
from core.fields import JSONCharMyField

class DailyBoutiqueStat(BaseModel):
    """ 每日精品商品及券数量统计
    规格统计数据结构:
        [
            {'sku_id':somevalue,'sku_stock_num':0, 'sku_sale_num':0, 'sku_refund_num':0}
        ]
    """
    model_id  = models.IntegerField(verbose_name=u'款式ID')
    stat_date = models.DateField(default=datetime.date.today,
                                 db_index=True, verbose_name=u'业务日期')

    model_stock_num = models.IntegerField(default=0, db_index=True, verbose_name=u'商品库存数量')
    model_sale_num  = models.IntegerField(default=0, db_index=True, verbose_name=u'商品销售数量')
    model_refund_num  = models.IntegerField(default=0, db_index=True, verbose_name=u'商品退款数')

    coupon_sale_num = models.IntegerField(default=0, db_index=True, verbose_name=u'券销售数量')
    coupon_use_num  = models.IntegerField(default=0, db_index=True, verbose_name=u'券使用数量')
    coupon_refund_num  = models.IntegerField(default=0, db_index=True, verbose_name=u'退券数量')

    sku_stats = JSONCharMyField(max_length=2048, default=[], blank=False, verbose_name=u"规格统计")

    # TODO@MENTION　需要补充券销售额, 退券金额

    class Meta:
        db_table = 'flashsale_daily_boutique_stat'
        unique_together = ['model_id', 'stat_date']
        app_label = 'daystats'
        verbose_name = u'精品/每日销售数量统计'
        verbose_name_plural = u'精品/每日销售数量统计列表'


class DailySkuAmountStat(BaseModel):
    """ 每日库存商品SKU销售统计 """
    sku_id    = models.IntegerField(verbose_name=u'规格ID')
    model_id  = models.IntegerField(db_index=True, default=0, verbose_name=u'款式ID')
    stat_date = models.DateField(default=datetime.date.today,
                                 db_index=True, verbose_name=u'业务日期')

    total_amount = models.IntegerField(default=0, verbose_name=u'总价值')
    total_cost = models.IntegerField(default=0, verbose_name=u'商品进价', help_text=u'实际采购价有波动，这里拿商品录入采购价做参考值')
    direct_payment = models.IntegerField(default=0, verbose_name=u'直接付款金额')
    coin_payment   = models.IntegerField(default=0, verbose_name=u'支付小鹿币', help_text=u'小鹿币只可用于买券')
    coupon_amount  = models.IntegerField(default=0, verbose_name=u'券使用面额')
    coupon_payment = models.IntegerField(default=0, db_index=True, verbose_name=u'券实际卖价')
    exchg_amount   = models.IntegerField(default=0, db_index=True, verbose_name=u'券兑换出额', help_text=u'扣除买券金额,已废弃')

    class Meta:
        db_table = 'flashsale_daily_skuamount_stat'
        unique_together = ['sku_id', 'stat_date']
        app_label = 'daystats'
        verbose_name = u'规格SKU/每日销售金额统计'
        verbose_name_plural = u'规格SKU/每日销售金额统计列表'


class DailySkuDeliveryStat(BaseModel):
    """ 每日库存商品SKU发货统计 """
    sku_id    = models.IntegerField(verbose_name=u'规格ID')
    model_id  = models.IntegerField(db_index=True, default=0, verbose_name=u'款式ID')
    stat_date = models.DateField(default=datetime.date.today,
                                 db_index=True, verbose_name=u'业务日期')

    days = models.IntegerField(default=0, db_index=True, verbose_name=u'间隔天数')
    post_num  = models.IntegerField(default=0, verbose_name=u'发货单数')
    wait_num = models.IntegerField(default=0, verbose_name=u'待发单数')

    class Meta:
        db_table = 'flashsale_daily_skudelivery_stat'
        unique_together = ['sku_id', 'stat_date', 'days']
        app_label = 'daystats'
        verbose_name = u'规格SKU/每日发货状态统计'
        verbose_name_plural = u'规格SKU/每日发货状态统计列表'


