# -*- coding:utf8 -*-
from __future__ import unicode_literals
from django.db import models
from shopback.trades.models import MergeTrade
from shopback import paramconfig as pcfg
from shopback.signals import rule_signal
import logging

logger = logging.getLogger('django.request')


class PinPaiTuan(models.Model):
    """ 参加品牌团入仓商品，规格"""

    outer_id = models.CharField(max_length=64, blank=True, db_index=True, verbose_name="商品外部编码")
    outer_sku_id = models.CharField(max_length=64, blank=True, db_index=True, verbose_name="规格外部编码")
    prod_sku_name = models.CharField(max_length=128, blank=True, db_index=True, verbose_name="商品规格名称")

    class Meta:
        db_table = 'shop_juhuasuan_pinpaituan'
        app_label = 'orders'
        verbose_name = '品牌团入仓商品'

    def __unicode__(self):
        return '<%s,%s,%s>' % (self.outer_id, self.outer_sku_id, self.prod_sku_name)


def order_match_juhuasuan_pinpaituan(sender, trade_id, *args, **kwargs):
    mergetrade = MergeTrade.objects.get(id=trade_id)
    if PinPaiTuan.objects.all().count() == 0:
        return

    full_match = False
    real_pay_orders = mergetrade.merge_orders.filter(gift_type=pcfg.REAL_ORDER_GIT_TYPE)

    for order in real_pay_orders:
        try:
            PinPaiTuan.objects.get(outer_id=order.outer_id, outer_sku_id=order.outer_sku_id)
        except:
            full_match &= False
        else:
            full_match &= True

    if full_match:
        raise Exception('订单满足需聚划算入仓')


rule_signal.connect(order_match_juhuasuan_pinpaituan, sender='ju_hua_suan',
                    dispatch_uid='rule_match_juhuasuan_pinpaituan')
