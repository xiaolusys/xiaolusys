# -*- coding:utf8 -*-
from __future__ import unicode_literals

import json
import time
import hashlib
import datetime
from django.db import models
from core.models import BaseModel
from core.fields import BigAutoField, BigForeignKey
from shopback.users.models import User as ShopUser
from shopback.items.models import Item, Product, ProductSku
from shopback import paramconfig as pcfg
from shopback.signals import merge_trade_signal
from common.utils import parse_datetime
from shopapp.taobao import apis
import logging

logger = logging.getLogger('django.request')

REFUND_STATUS = (
    (pcfg.NO_REFUND, '没有退款'),
    (pcfg.REFUND_WAIT_SELLER_AGREE, '等待卖家同意'),
    (pcfg.REFUND_WAIT_RETURN_GOODS, '等待买家退货'),
    (pcfg.REFUND_CONFIRM_GOODS, '卖家确认收货'),
    (pcfg.REFUND_REFUSE_BUYER, '买家拒绝退款'),
    (pcfg.REFUND_CLOSED, '退款已关闭'),
    (pcfg.REFUND_SUCCESS, '退款已成功'),
)

TAOBAO_TRADE_STATUS = (
    (pcfg.TRADE_NO_CREATE_PAY, '没有创建支付宝交易'),
    (pcfg.WAIT_BUYER_PAY, '等待买家付款'),
    (pcfg.WAIT_SELLER_SEND_GOODS, '等待卖家发货'),
    (pcfg.WAIT_BUYER_CONFIRM_GOODS, '等待买家确认收货'),
    (pcfg.TRADE_BUYER_SIGNED, '买家已签收,货到付款专用'),
    (pcfg.TRADE_FINISHED, '交易成功'),
    (pcfg.TRADE_CLOSED, '付款以后用户退款成功，交易自动关闭'),
    (pcfg.TRADE_CLOSED_BY_TAOBAO, '付款以前，卖家或买家主动关闭交易'),
)

STEP_TRADE_STATUS = (
    (pcfg.FRONT_NOPAID_FINAL_NOPAID, '定金未付尾款未付'),
    (pcfg.FRONT_PAID_FINAL_NOPAID, '定金已付尾款未付'),
    (pcfg.FRONT_PAID_FINAL_PAID, '定金和尾款都付'),
)

STAGE_CHOICES = (
    (0, u'需创建发货sku单'),
    (1, u'已创建发货sku单'),
    (2, u'已用老办法处理')
)


class Trade(models.Model):
    YOUNI_SELLER_NICK = u'优尼世界旗舰店'
    id = models.BigIntegerField(primary_key=True)
    user = models.ForeignKey(ShopUser, null=True, related_name='trades')
    seller_id = models.CharField(max_length=64, blank=True)
    seller_nick = models.CharField(max_length=64, blank=True)
    buyer_nick = models.CharField(max_length=64, blank=True)
    type = models.CharField(max_length=32, blank=True)

    payment = models.FloatField(default=0.0)
    discount_fee = models.FloatField(default=0.0)
    adjust_fee = models.FloatField(default=0.0)
    post_fee = models.FloatField(default=0.0)
    total_fee = models.FloatField(default=0.0)

    buyer_obtain_point_fee = models.FloatField(default=0.0)
    point_fee = models.FloatField(default=0.0)
    real_point_fee = models.FloatField(default=0.0)
    commission_fee = models.FloatField(default=0.0)

    created = models.DateTimeField(null=True, blank=True)
    pay_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    modified = models.DateTimeField(null=True, blank=True)
    consign_time = models.DateTimeField(null=True, blank=True)
    send_time = models.DateTimeField(null=True, blank=True)

    buyer_message = models.TextField(max_length=1000, blank=True)
    buyer_memo = models.TextField(max_length=1000, blank=True)
    seller_memo = models.TextField(max_length=1000, blank=True)
    seller_flag = models.IntegerField(null=True, help_text=u'自订订单标记')

    is_brand_sale = models.BooleanField(default=False)
    is_force_wlb = models.BooleanField(default=False)
    trade_from = models.CharField(default='', max_length=32, blank=True)

    is_lgtype = models.BooleanField(default=False)
    lg_aging = models.DateTimeField(null=True, blank=True)
    lg_aging_type = models.CharField(max_length=20, blank=True)

    buyer_rate = models.BooleanField(default=False)
    seller_rate = models.BooleanField(default=False)
    seller_can_rate = models.BooleanField(default=False)
    is_part_consign = models.BooleanField(default=False)

    seller_cod_fee = models.FloatField(default=0.0)
    buyer_cod_fee = models.FloatField(default=0.0)
    cod_fee = models.FloatField(default=0.0)
    cod_status = models.CharField(max_length=32, blank=True)

    shipping_type = models.CharField(max_length=12, blank=True)
    buyer_alipay_no = models.CharField(max_length=128, blank=True)
    receiver_name = models.CharField(max_length=64, blank=True)
    receiver_state = models.CharField(max_length=16, blank=True)
    receiver_city = models.CharField(max_length=16, blank=True)
    receiver_district = models.CharField(max_length=16, blank=True)

    receiver_address = models.CharField(max_length=128, blank=True)
    receiver_zip = models.CharField(max_length=10, blank=True)
    receiver_mobile = models.CharField(max_length=24, blank=True)
    receiver_phone = models.CharField(max_length=20, blank=True)
    user_address_unikey = models.CharField(max_length=40, null=True, default=None, db_index=True, verbose_name=u'地址唯一标识', help_text=u'用户地址sha1')
    user_unikey = models.CharField(max_length=40, null=True, default=None, db_index=True, verbose_name=u'用户唯一标识', help_text=u'用户姓名电话sha1')
    step_paid_fee = models.FloatField(default=0.0)
    step_trade_status = models.CharField(max_length=32, choices=STEP_TRADE_STATUS, blank=True)
    status = models.CharField(max_length=32, choices=TAOBAO_TRADE_STATUS, blank=True)

    class Meta:
        db_table = 'shop_orders_trade'
        app_label = 'orders'
        verbose_name = u'淘宝订单'
        verbose_name_plural = u'淘宝订单列表'

    def __unicode__(self):
        return str(self.id)

    @classmethod
    def get_or_create(cls, trade_id, user_id):

        from shopback.trades.models import MergeTrade
        user = ShopUser.objects.get(nick=user_id)
        trade, state = cls.objects.get_or_create(id=trade_id, user=user)
        try:
            MergeTrade.objects.get(tid=trade_id)
        except MergeTrade.DoesNotExist:
            try:
                response = apis.taobao_trade_fullinfo_get(tid=trade_id, tb_user_id=user_id)
                trade_dict = response['trade_fullinfo_get_response']['trade']
                trade = Trade.save_trade_through_dict(user_id, trade_dict)
            except Exception, exc:
                logger.error('backend update trade (tid:%s)error' % str(trade_id), exc_info=True)
        return trade

    @staticmethod
    def seller():
        if not hasattr(Trade, '_seller_'):
            Trade._seller_ = ShopUser.objects.get(uid=Trade.YOUNI_SELLER_ID)
        return Trade._seller_

    @classmethod
    def save_trade_through_dict(cls, user_id, trade_dict):

        trade, state = cls.objects.get_or_create(pk=trade_dict['tid'])
        trade.user = ShopUser.objects.get(visitor_id=user_id)
        trade.seller_id = user_id
        for k, v in trade_dict.iteritems():
            hasattr(trade, k) and setattr(trade, k, v)

        if trade_dict.get('pay_time', ''):
            dt = parse_datetime(trade_dict['pay_time'])
            trade.year = dt.year
            trade.hour = dt.hour
            trade.month = dt.month
            trade.day = dt.day
            trade.week = time.gmtime(time.mktime(dt.timetuple()))[7] / 7 + 1

        trade.created = parse_datetime(trade_dict['created'])
        trade.pay_time = parse_datetime(trade_dict['pay_time']) \
            if trade_dict.get('pay_time', None) else None
        trade.end_time = parse_datetime(trade_dict['end_time']) \
            if trade_dict.get('end_time', None) else None
        trade.modified = parse_datetime(trade_dict['modified']) \
            if trade_dict.get('modified', None) else None
        trade.consign_time = parse_datetime(trade_dict['consign_time']) \
            if trade_dict.get('consign_time', None) else None
        trade.send_time = parse_datetime(trade_dict['send_time']) \
            if trade_dict.get('send_time', None) else None
        trade.lg_aging = parse_datetime(trade_dict['lg_aging']) \
            if trade_dict.get('lg_aging', None) else None
        trade.save()

        for o in trade_dict['orders']['order']:
            order, state = Order.objects.get_or_create(pk=o['oid'])
            order.seller_nick = trade_dict['seller_nick']
            order.buyer_nick = trade_dict['buyer_nick']
            order.trade = trade
            for k, v in o.iteritems():
                hasattr(order, k) and setattr(order, k, v)
            order.outer_id = o.get('outer_iid', '')
            order.year = trade.year
            order.month = trade.month
            order.day = trade.day
            order.week = trade.week
            order.hour = trade.hour
            order.created = trade.created
            order.pay_time = trade.pay_time
            order.consign_time = trade.consign_time
            order.save()

        merge_trade_signal.send(sender=Trade, trade=trade)
        return trade

    def get_address_unikey(self):
        address = self.receiver_state + self.receiver_city + self.receiver_district + self.receiver_address
        return hashlib.sha1(address).hexdigest()

    def get_user_unikey(self):
        user = self.receiver_name + self.receiver_phone + self.YOUNI_SELLER_NICK
        return hashlib.sha1(user).hexdigest()

    @staticmethod
    def seller():
        if not hasattr(Trade, '_seller_'):
            Trade._seller_ = ShopUser.objects.get(nick=Trade.YOUNI_SELLER_NICK)
        return Trade._seller_


class Order(models.Model):
    oid = models.BigIntegerField(primary_key=True)
    cid = models.BigIntegerField(null=True)

    trade = BigForeignKey(Trade, null=True, related_name='trade_orders')

    num_iid = models.CharField(max_length=64, blank=True)
    title = models.CharField(max_length=128)
    price = models.FloatField(default=0.0)

    item_meal_id = models.IntegerField(null=True)
    sku_id = models.CharField(max_length=20, blank=True)
    num = models.IntegerField(null=True, default=0)

    outer_sku_id = models.CharField(max_length=20, blank=True)
    total_fee = models.FloatField(default=0.0)

    payment = models.FloatField(default=0.0)
    discount_fee = models.FloatField(default=0.0)
    adjust_fee = models.FloatField(default=0.0)

    sku_properties_name = models.TextField(max_length=256, blank=True)
    refund_id = models.BigIntegerField(null=True)

    is_oversold = models.BooleanField(default=False)
    is_service_order = models.BooleanField(default=False)

    item_meal_name = models.CharField(max_length=88, blank=True)
    pic_path = models.CharField(max_length=128, blank=True)

    seller_nick = models.CharField(max_length=32, blank=True)
    buyer_nick = models.CharField(max_length=32, blank=True)

    refund_status = models.CharField(max_length=40, choices=REFUND_STATUS, blank=True)
    outer_id = models.CharField(max_length=64, blank=True)

    created = models.DateTimeField(null=True, blank=True)
    pay_time = models.DateTimeField(db_index=True, null=True, blank=True)
    consign_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=32, choices=TAOBAO_TRADE_STATUS, blank=True)

    stage = models.IntegerField(default=0, choices=STAGE_CHOICES, db_index=True, verbose_name=u'发货进度', help_text=u'0未处理1发货中2已完结')

    class Meta:
        db_table = 'shop_orders_order'
        app_label = 'orders'
        verbose_name = u'淘宝订单商品'
        verbose_name_plural = u'淘宝订单商品列表'

    def __unicode__(self):
        return str(self.oid)

    @property
    def properties_values(self):
        properties_list = self.sku_properties_name.split(';')
        value_list = []
        for properties in properties_list:
            values = properties.split(':')
            value_list.append(values[1] if len(values) == 2 else properties)
        return ' '.join(value_list)

    @property
    def sku(self):
        if not hasattr(self, '_sku_'):
            otps = self.outer_sku_id.split('.')
            if len(otps) > 1:
                self._sku_ = ProductSku.objects.filter(product__outer_id=otps[0], outer_id=otps[1]).first()
            else:
                self._sku_ = ProductSku.objects.filter(product__outer_id=self.outer_id, outer_id=self.outer_sku_id).first()
        return self._sku_

    @property
    def product(self):
        if not hasattr(self, '_product_'):
            self._product_ = Product.objects.filter(outer_id=self.outer_id).first()
        return self._product_

    def get_tb_oid(self):
        return 'tb' + str(self.oid)

    def has_psi_created(self):
        from shopback.trades.models import PackageSkuItem, PSI_TYPE
        return PackageSkuItem.objects.filter(oid=self.get_tb_oid()).exists()

    def create_package_sku_item(self):
        if self.stage > 0:
            return
        if self.has_psi_created():
            return
        # 防错　如果mergeOrder已发货，则不再产生成PackageSkuItem
        from shopback.trades.models import PackageSkuItem, PSI_TYPE, MergeOrder, MergeTrade
        merge_order = MergeOrder.objects.filter(oid=self.oid).first()
        if merge_order.is_sent() or merge_order.merge_trade.is_sent():
            return
        ware_by = self.sku.ware_by
        sku_item = PackageSkuItem(sale_order_id=None, ware_by=ware_by, oid=self.get_tb_oid())
        sku_item.sku_id = self.sku.id
        sku_item.product = self.product
        sku_item.outer_sku_id = self.outer_sku_id
        sku_item.outer_id = self.product.outer_id
        sku_item.num = self.num
        sku_item.type = PSI_TYPE.TIANMAO
        sku_item.package_order_id
        sku_item.package_order_pid
        sku_item.ware_by = ware_by
        # sku_item.cid = None
        sku_item.title = self.product.title()
        sku_item.sku_properties_name = self.sku.properties_name
        sku_item.pic_path = self.sku.product.pic_path
        sku_item.pay_time = self.trade.pay_time
        sku_item.receiver_mobile = self.trade.receiver_mobile
        # sku_item.out_sid
        # sku_item.logistics_company_name
        sku_item.price = self.price
        sku_item.total_fee = self.payment
        sku_item.payment = self.payment
        sku_item.discount_fee = self.discount_fee
        sku_item.sale_trade_id = 'tb' + str(self.trade.id)
        sku_item.save()
        sku_item.set_status_init_assigned()
        # PackageSkuItem.batch_merge(type=PSI_TYPE.TIANMAO)
        self.stage = 1
        self.save()
        return sku_item

    def get_package_item(self):
        from shopback.trades.models import PackageSkuItem, MergeOrder
        if self.statge in [0, 2]:
            return MergeOrder.objects.filter(oid=self.oid).first()
        else:
            return PackageSkuItem.objects.filter(oid=self.get_tb_oid()).first()

    def need_send(self):
        return self.status == pcfg.WAIT_SELLER_SEND_GOODS

    def finish_sent(self):
        self.status = pcfg.WAIT_BUYER_CONFIRM_GOODS
        self.consign_time = datetime.datetime.now()
        self.save()