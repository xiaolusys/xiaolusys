#-*- coding:utf8 -*-
import json
import time
from auth.utils import parse_datetime
from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from shopback.users.models import User
from shopback.items.models import Item
from shopback.signals import merge_trade_signal
from auth import apis
import logging

logger = logging.getLogger('orders.handler')



NO_REFUND = 'NO_REFUND'
REFUND_WAIT_SELLER_AGREE  = 'WAIT_SELLER_AGREE'
REFUND_WAIT_RETURN_GOODS  = 'WAIT_BUYER_RETURN_GOODS'
REFUND_CONFIRM_GOODS      = 'WAIT_SELLER_CONFIRM_GOODS'
REFUND_REFUSE_BUYER       = 'SELLER_REFUSE_BUYER'
REFUND_CLOSED   = 'CLOSED'
REFUND_SUCCESS  = 'SUCCESS'
REFUND_STATUS = (
    (NO_REFUND,'没有退款'),
    (REFUND_WAIT_SELLER_AGREE,'等待卖家同意'),
    (REFUND_WAIT_RETURN_GOODS,'等待买家退货'),
    (REFUND_CONFIRM_GOODS,'卖家确认收货'),
    (REFUND_REFUSE_BUYER,'买家拒绝退款'),
    (REFUND_CLOSED,'退款已关闭'),
    (REFUND_SUCCESS,'退款已成功'),
)
REFUND_APPROVAL_STATUS = [REFUND_WAIT_RETURN_GOODS,REFUND_CONFIRM_GOODS,REFUND_SUCCESS]

TRADE_NO_CREATE_PAY = 'TRADE_NO_CREATE_PAY'
WAIT_BUYER_PAY      = 'WAIT_BUYER_PAY'
WAIT_SELLER_SEND_GOODS = 'WAIT_SELLER_SEND_GOODS'
WAIT_BUYER_CONFIRM_GOODS = 'WAIT_BUYER_CONFIRM_GOODS'
TRADE_BUYER_SIGNED = 'TRADE_BUYER_SIGNED'
TRADE_FINISHED     = 'TRADE_FINISHED'
TRADE_CLOSED       = 'TRADE_CLOSED'
TRADE_CLOSED_BY_TAOBAO = 'TRADE_CLOSED_BY_TAOBAO'

TAOBAO_TRADE_STATUS = (
    ('TRADE_NO_CREATE_PAY','没有创建支付宝交易'),
    ('WAIT_BUYER_PAY','等待买家付款'),
    ('WAIT_SELLER_SEND_GOODS','等待卖家发货'),
    ('WAIT_BUYER_CONFIRM_GOODS','等待买家确认收货'),
    ('TRADE_BUYER_SIGNED','买家已签收,货到付款专用'),
    ('TRADE_FINISHED','交易成功'),
    ('TRADE_CLOSED','付款以后用户退款成功，交易自动关闭'),
    ('TRADE_CLOSED_BY_TAOBAO','付款以前，卖家或买家主动关闭交易'),
)

ORDER_SUCCESS_STATUS  = (WAIT_SELLER_SEND_GOODS,WAIT_BUYER_CONFIRM_GOODS,TRADE_BUYER_SIGNED,TRADE_FINISHED)
ORDER_UNFINISH_STATUS = (WAIT_SELLER_SEND_GOODS,WAIT_BUYER_CONFIRM_GOODS,TRADE_BUYER_SIGNED)
ORDER_POST_STATUS     = (WAIT_BUYER_CONFIRM_GOODS,TRADE_BUYER_SIGNED,TRADE_FINISHED)
ORDER_OK_STATUS       = (TRADE_FINISHED,TRADE_CLOSED)
ORDER_FINISH_STATUS   = TRADE_FINISHED
ORDER_REFUND_STATUS   = TRADE_CLOSED
ORDER_UNPAY_STATUS    = WAIT_BUYER_PAY

class Trade(models.Model):

    id           =  BigIntegerAutoField(primary_key=True)
    user         =  models.ForeignKey(User,null=True,related_name='trades')

    seller_id    =  models.CharField(max_length=64,db_index=True,blank=True)
    seller_nick  =  models.CharField(max_length=64,db_index=True,blank=True)
    buyer_nick   =  models.CharField(max_length=64,db_index=True,blank=True)
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

    seller_cod_fee = models.CharField(max_length=10,blank=True)
    buyer_cod_fee  = models.CharField(max_length=10,blank=True)
    cod_fee        = models.CharField(max_length=10,blank=True)
    cod_status     = models.CharField(max_length=32,blank=True)
    
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

    status      =  models.CharField(max_length=32,choices=TAOBAO_TRADE_STATUS,blank=True)

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
                logger.error('backend update trade (tid:%s)error'%str(trade_id),exc_info=True)
        return trade


    @classmethod
    def save_trade_through_dict(cls,user_id,trade_dict):
        
        trade,state = cls.objects.get_or_create(pk=trade_dict['tid'])
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

        for o in trade_dict['orders']['order']:
            order,state = Order.objects.get_or_create(pk=o['oid'])
            order.seller_nick = trade_dict['seller_nick']
            order.buyer_nick  = trade_dict['buyer_nick']
            order.trade       = trade
            if not state:
                o.pop('sku_properties_name',None)
            for k,v in o.iteritems():
                hasattr(order,k) and setattr(order,k,v)
            order.outer_id = o.get('outer_iid','')
            order.year  = trade.year
            order.month = trade.month
            order.day   = trade.day
            order.week  = trade.week
            order.hour  = trade.hour
            order.created   = trade.created
            order.pay_time  = trade.pay_time
            order.consign_time   = trade.consign_time
            order.save()
            
        merge_trade_signal.send(sender=Trade,trade=trade)
        return trade




class Order(models.Model):

    oid   = BigIntegerAutoField(primary_key=True)
    cid    = models.BigIntegerField(null=True)

    trade = BigIntegerForeignKey(Trade,null=True,related_name='trade_orders')

    num_iid  = models.CharField(max_length=64,blank=True)
    title =  models.CharField(max_length=128)
    price = models.CharField(max_length=12,blank=True)

    item_meal_id = models.IntegerField(null=True)
    sku_id = models.CharField(max_length=20,blank=True)
    num = models.IntegerField(null=True,default=0)

    outer_sku_id = models.CharField(max_length=20,blank=True)
    total_fee = models.CharField(max_length=12,blank=True)

    payment = models.CharField(max_length=12,blank=True)
    discount_fee = models.CharField(max_length=12,blank=True)
    adjust_fee = models.CharField(max_length=12,blank=True)

    sku_properties_name = models.TextField(max_length=256,blank=True)
    refund_id = models.BigIntegerField(null=True)

    is_oversold = models.BooleanField()
    is_service_order = models.BooleanField()

    item_meal_name = models.CharField(max_length=88,blank=True)
    pic_path = models.CharField(max_length=128,blank=True)

    seller_nick = models.CharField(max_length=32,blank=True,db_index=True)
    buyer_nick  = models.CharField(max_length=32,db_index=True,blank=True)

    refund_status = models.CharField(max_length=40,choices=REFUND_STATUS,blank=True)
    outer_id = models.CharField(max_length=64,blank=True)
    
    year  = models.IntegerField(null=True,db_index=True)
    month = models.IntegerField(null=True,db_index=True)
    week  = models.IntegerField(null=True,db_index=True)
    day   = models.IntegerField(null=True,db_index=True)
    hour  = models.CharField(max_length=5,blank=True,db_index=True)
    
    created       =  models.DateTimeField(db_index=True,null=True,blank=True)
    pay_time      =  models.DateTimeField(db_index=True,null=True,blank=True)
    consign_time  =  models.DateTimeField(db_index=True,null=True,blank=True)
    
    status = models.CharField(max_length=32,choices=TAOBAO_TRADE_STATUS,blank=True)

    class Meta:
        db_table = 'shop_orders_order'

    def __unicode__(self):
        return str(self.oid)
    
    @property
    def properties_values(self):
        properties_list = self.sku_properties_name.split(';')
        value_list = []
        for properties in properties_list:
            values = properties.split(':')
            value_list.append( values[1] if len(values)==2 else properties)
        return ' '.join(value_list)




