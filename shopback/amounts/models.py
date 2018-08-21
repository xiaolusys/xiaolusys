# -*- coding:utf8 -*-
from __future__ import unicode_literals

import json
import time
from common.utils import parse_datetime
from django.db import models
from shopback.users.models import User
from shopback.items.models import Item
import logging

logger = logging.getLogger('amounts.handler')


class TradeAmount(models.Model):
    tid = models.BigIntegerField(primary_key=True)

    user = models.ForeignKey(User, null=True, related_name='trade_amounts')
    buyer_cod_fee = models.CharField(max_length=10, blank=True)
    seller_cod_fee = models.CharField(max_length=10, blank=True)
    express_agency_fee = models.CharField(max_length=10, blank=True)

    alipay_no = models.CharField(max_length=64, blank=True)

    total_fee = models.CharField(max_length=10, blank=True)
    post_fee = models.CharField(max_length=10, blank=True)
    cod_fee = models.CharField(max_length=10, blank=True)
    payment = models.CharField(max_length=10, blank=True)

    commission_fee = models.CharField(max_length=10, blank=True)
    buyer_obtain_point_fee = models.CharField(max_length=10, blank=True)
    promotion_details = models.TextField(max_length=500, blank=True)

    created = models.DateTimeField(null=True)
    pay_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)

    year = models.IntegerField(null=True, db_index=True)
    month = models.IntegerField(null=True, db_index=True)
    week = models.IntegerField(null=True, db_index=True)
    day = models.IntegerField(null=True, db_index=True)
    hour = models.CharField(max_length=5, blank=True, db_index=True)

    class Meta:
        db_table = 'shop_amounts_tradeamount'
        app_label = 'amounts'

    def __unicode__(self):
        return str(self.tid)

    @classmethod
    def get_or_create(cls, user_id, trade_id):
        trade_amount, state = cls.objects.get_or_create(pk=trade_id)
        if state:
            try:
                response = apis.taobao_trade_amount_get(tid=trade_id, tb_user_id=user_id)
                trade_amount_dict = response['trade_amount_get_response']['trade_amount']
                trade_amount = cls.save_trade_amount_through_dict(user_id, trade_amount_dict)
            except Exception, exc:
                logger.error('淘宝后台更新该交易帐务(tid:%s)出错'.decode('utf8') % str(trade_id), exc_info=True)
        return trade_amount

    @classmethod
    def save_trade_amount_through_dict(cls, user_id, trade_amount_dict):

        trade_amount, state = cls.objects.get_or_create(pk=trade_amount_dict['tid'])
        trade_amount.user = User.objects.get(visitor_id=user_id)
        order_amounts = trade_amount_dict.pop('order_amounts')
        for k, v in trade_amount_dict.iteritems():
            hasattr(trade_amount, k) and setattr(trade_amount, k, v)

        dt = parse_datetime(trade_amount_dict['created'])
        trade_amount.year = dt.year
        trade_amount.hour = dt.hour
        trade_amount.month = dt.month
        trade_amount.day = dt.day
        trade_amount.week = time.gmtime(time.mktime(dt.timetuple()))[7] / 7 + 1

        trade_amount.created = parse_datetime(trade_amount_dict['created'])
        trade_amount.pay_time = parse_datetime(trade_amount_dict['pay_time']) \
            if trade_amount_dict.get('pay_time', None) else None
        trade_amount.end_time = parse_datetime(trade_amount_dict['end_time']) \
            if trade_amount_dict.get('end_time', None) else None

        trade_amount.promotion_details = json.dumps(trade_amount_dict.get('promotion_details', None))
        trade_amount.save()

        order_amount = OrderAmount()
        order_amount.trade_amount = trade_amount

        for o in order_amounts['order_amount']:
            for k, v in o.iteritems():
                hasattr(order_amount, k) and setattr(order_amount, k, v)

            order_amount.save()

        return trade_amount


class OrderAmount(models.Model):
    oid = models.BigIntegerField(primary_key=True)

    num_iid = models.BigIntegerField(null=True)
    trade_amount = models.ForeignKey(TradeAmount, related_name='order_amounts')

    title = models.CharField(max_length=64, blank=True)
    sku_id = models.BigIntegerField(null=True)
    sku_properties_name = models.CharField(max_length=128, blank=True)

    num = models.IntegerField(null=True)
    price = models.CharField(max_length=10, blank=True)

    payment = models.CharField(max_length=10, blank=True)
    discount_fee = models.CharField(max_length=10, blank=True)
    adjust_fee = models.CharField(max_length=10, blank=True)

    promotion_name = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = 'shop_amounts_orderamount'
        app_label = 'amounts'

    def __unicode__(self):
        return str(self.oid)
