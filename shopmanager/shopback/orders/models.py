#-*- coding:utf8 -*-
import json
import time
from auth.utils import parse_datetime
from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from shopback.users.models import User
from shopback.items.models import Item
from auth import apis
import logging

logger = logging.getLogger('orders.handler')


ORDER_SUCCESS_STATUS  = ['WAIT_SELLER_SEND_GOODS','WAIT_BUYER_CONFIRM_GOODS','TRADE_BUYER_SIGNED','TRADE_FINISHED']
ORDER_UNFINISH_STATUS = ['WAIT_SELLER_SEND_GOODS','WAIT_BUYER_CONFIRM_GOODS','TRADE_BUYER_SIGNED']
ORDER_OK_STATUS       = ['TRADE_FINISHED','TRADE_CLOSED']
ORDER_FINISH_STATUS   = 'TRADE_FINISHED'
ORDER_REFUND_STATUS   = 'TRADE_CLOSED'
ORDER_UNPAY_STATUS    = 'WAIT_BUYER_PAY'


class Trade(models.Model):

    id           =  BigIntegerAutoField(primary_key=True)

    user         =  models.ForeignKey(User,null=True,related_name='trades')

    seller_id    =  models.CharField(max_length=64,blank=True)
    seller_nick  =  models.CharField(max_length=64,blank=True)
    buyer_nick   =  models.CharField(max_length=64,blank=True)
    type         =  models.CharField(max_length=32,blank=True)

    year  = models.IntegerField(null=True,db_index=True)
    month = models.IntegerField(null=True,db_index=True)
    week  = models.IntegerField(null=True,db_index=True)
    day   = models.IntegerField(null=True,db_index=True)
    hour  = models.CharField(max_length=5,blank=True,db_index=True)

    payment      =  models.CharField(max_length=10,blank=True)
    discount_fee =  models.CharField(max_length=10,blank=True)
    adjust_fee   =  models.CharField(max_length=10,blank=True)
    post_fee    =  models.CharField(max_length=10,blank=True)
    total_fee   =  models.CharField(max_length=10,blank=True)

    buyer_obtain_point_fee  =  models.CharField(max_length=10,blank=True)
    point_fee        =  models.CharField(max_length=10,blank=True)
    real_point_fee   =  models.CharField(max_length=10,blank=True)
    commission_fee   =  models.CharField(max_length=10,blank=True)

    created       =  models.DateTimeField(db_index=True,null=True,blank=True)
    pay_time      =  models.DateTimeField(null=True,blank=True)
    end_time      =  models.DateTimeField(db_index=True,null=True,blank=True)
    modified      =  models.DateTimeField(db_index=True,null=True,blank=True)
    consign_time  =  models.DateTimeField(db_index=True,null=True,blank=True)

    buyer_message    =  models.TextField(max_length=1000,blank=True)
    buyer_memo       =  models.TextField(max_length=1000,blank=True)
    seller_memo      =  models.TextField(max_length=1000,blank=True)

    shipping_type    =  models.CharField(max_length=12,blank=True)
    buyer_alipay_no  =  models.CharField(max_length=128,blank=True)
    receiver_name    =  models.CharField(max_length=64,blank=True)
    receiver_state   =  models.CharField(max_length=16,blank=True)
    receiver_city    =  models.CharField(max_length=16,blank=True)
    receiver_district  =  models.CharField(max_length=16,blank=True)

    receiver_address   =  models.CharField(max_length=128,blank=True)
    receiver_zip       =  models.CharField(max_length=10,blank=True)
    receiver_mobile    =  models.CharField(max_length=20,blank=True)
    receiver_phone     =  models.CharField(max_length=20,blank=True)

    status      =  models.CharField(max_length=32,blank=True)

    class Meta:
        db_table = 'shop_orders_trade'

    def __unicode__(self):
        return str(self.id)

    @classmethod
    def get_or_create(cls,trade_id,user_id):
        user = User.objects.get(visitor_id=user_id)
        trade,state = cls.objects.get_or_create(pk=trade_id,user=user)
        if state:
            try:
                response    = apis.taobao_trade_fullinfo_get(tid=trade_id,tb_user_id=user_id)
                trade_dict  = response['trade_fullinfo_get_response']['trade']
                trade = Trade.save_trade_through_dict(user_id,trade_dict)
            except Exception,exc:
                logger.error('淘宝后台更新交易信息(tid:%s)出错'%str(trade_id),exc_info=True)
        return trade


    @classmethod
    def save_trade_through_dict(cls,user_id,trade_dict):

        trade,state = Trade.objects.get_or_create(pk=trade_dict['tid'])
        trade.user  = User.objects.get(visitor_id=user_id)
        trade.seller_id   = user_id
        for k,v in trade_dict.iteritems():
            hasattr(trade,k) and setattr(trade,k,v)

        dt = parse_datetime(trade_dict['created'])
        trade.year  = dt.year
        trade.hour  = dt.hour
        trade.month = dt.month
        trade.day   = dt.day
        trade.week  = time.gmtime(time.mktime(dt.timetuple()))[7]/7+1
        
        trade.created  = parse_datetime(trade_dict['created'])
        trade.pay_time = parse_datetime(trade_dict['pay_time']) \
                           if trade_dict.get('pay_time',None) else None
        trade.end_time = parse_datetime(trade_dict['end_time']) \
                           if trade_dict.get('end_time',None) else None
        trade.modified = parse_datetime(trade_dict['modified']) \
                           if trade_dict.get('modified',None) else None
        trade.consign_time = parse_datetime(trade_dict['consign_time']) \
                           if trade_dict.get('consign_time',None) else None
        trade.save()

        order = Order()
        order.seller_nick = trade_dict['seller_nick']
        order.buyer_nick  = trade_dict['buyer_nick']
        order.trade       = trade

        for o in trade_dict['orders']['order']:
            for k,v in o.iteritems():
                hasattr(order,k) and setattr(order,k,v)

            order.item = Item.get_or_create(user_id,o['num_iid'])
            order.save()

        return trade




class Order(models.Model):

    oid   = BigIntegerAutoField(primary_key=True)
    cid    = models.BigIntegerField(null=True)

    trade = BigIntegerForeignKey(Trade,null=True,related_name='trade_orders')
    item  = models.ForeignKey(Item,null=True,related_name='orders')

    num_iid  = models.CharField(max_length=64,blank=True)
    title =  models.CharField(max_length=128)
    price = models.CharField(max_length=12,blank=True)

    item_meal_id = models.IntegerField(null=True)
    sku_id = models.CharField(max_length=20,blank=True)
    num = models.IntegerField(null=True)

    outer_sku_id = models.CharField(max_length=20,blank=True)
    total_fee = models.CharField(max_length=12,blank=True)

    payment = models.CharField(max_length=12,blank=True)
    discount_fee = models.CharField(max_length=12,blank=True)
    adjust_fee = models.CharField(max_length=12,blank=True)

    modified = models.CharField(max_length=19,blank=True)
    sku_properties_name = models.TextField(max_length=256,blank=True)
    refund_id = models.BigIntegerField(null=True)

    is_oversold = models.BooleanField()
    is_service_order = models.BooleanField()

    item_meal_name = models.CharField(max_length=88,blank=True)
    pic_path = models.CharField(max_length=128,blank=True)

    seller_nick = models.CharField(max_length=32,blank=True,db_index=True)
    buyer_nick  = models.CharField(max_length=32,blank=True)

    refund_status = models.CharField(max_length=40,blank=True)
    outer_id = models.CharField(max_length=64,blank=True)

    status = models.CharField(max_length=32,blank=True)

    class Meta:
        db_table = 'shop_orders_order'

    def __unicode__(self):
        return str(self.oid)








#class TradeSerialId(models.Model):
#
#    year  = models.IntegerField()
#    month = models.IntegerField()
#    day   = models.IntegerField()
#
#    serial_no = models.IntegerField(default=1)
#
#    class Meta:
#        db_table = 'shop_tradeserialid'
#        unique_together = ("year","month","day")