#-*- coding:utf-8 -*-
import time
import json
import datetime
from django.db import models
from django.db.models import Q,Sum
from django.db.models.signals import post_save
from django.db import IntegrityError, transaction

from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from shopback.logistics.models import LogisticsCompany


class SaleTrade(models.Model):
    
    WX_TYPE = 'wx_pub'
    ALIPAY_TYPE = 'alipay_pub'
    UPMP_TYPE = 'upmp_wap'
    
    CHANNEL_CHOICES = (
        (WX_TYPE,u'微信小店'),
        (ALIPAY_TYPE,u'支付宝'),
        (UPMP_TYPE,u'银联'),
    )
    
    TRADE_NO_CREATE_PAY = 0
    WAIT_BUYER_PAY = 1
    WAIT_SELLER_SEND_GOODS = 2
    WAIT_BUYER_CONFIRM_GOODS = 3
    TRADE_BUYER_SIGNED = 4
    TRADE_FINISHED = 5
    TRADE_CLOSED = 6
    TRADE_CLOSED_BY_TAOBAO = 7
    
    TRADE_STATUS = (
        (TRADE_NO_CREATE_PAY,u'订单创建'),
        (WAIT_BUYER_PAY,u'待付款'),
        (WAIT_SELLER_SEND_GOODS,u'待发货'),
        (WAIT_BUYER_CONFIRM_GOODS,u'待确认收货'),
        (TRADE_BUYER_SIGNED,u'货到付款签收'),
        (TRADE_FINISHED,u'交易成功'),
        (TRADE_CLOSED,u'退款交易关闭'),
        (TRADE_CLOSED_BY_TAOBAO,u'未付款关闭'),
    )

    
    id    = BigIntegerAutoField(primary_key=True,verbose_name=u'订单ID')
    
    tid   = models.CharField(max_length=32,
                             verbose_name=u'原单ID')  
    buyer_nick  = models.CharField(max_length=64,db_index=True,blank=True,verbose_name=u'买家昵称')
    
    channel     = models.CharField(max_length=16,choices=CHANNEL_CHOICES,
                                  blank=True,verbose_name=u'付款类型')
    
    payment    =   models.FloatField(default=0.0,verbose_name=u'实付款')
    post_fee   =   models.FloatField(default=0.0,verbose_name=u'物流费用')
    total_fee  =   models.FloatField(default=0.0,verbose_name=u'总费用')
    
    buyer_message = models.TextField(max_length=1000,blank=True,verbose_name=u'买家留言')
    seller_memo   = models.TextField(max_length=1000,blank=True,verbose_name=u'卖家备注')
    
    created      = models.DateTimeField(null=True,blank=True,verbose_name=u'生成日期')
    pay_time     = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'付款日期')
    modified     = models.DateTimeField(null=True,blank=True,verbose_name=u'修改日期')
    consign_time = models.DateTimeField(null=True,blank=True,verbose_name=u'发货日期')
    
    out_sid         = models.CharField(max_length=64,db_index=True,
                                       blank=True,verbose_name=u'物流编号')
    logistics_company  = models.ForeignKey(LogisticsCompany,null=True,
                                           blank=True,verbose_name=u'物流公司')
    receiver_name    =  models.CharField(max_length=25,
                                         blank=True,verbose_name=u'收货人姓名')
    receiver_state   =  models.CharField(max_length=16,blank=True,verbose_name=u'省')
    receiver_city    =  models.CharField(max_length=16,blank=True,verbose_name=u'市')
    receiver_district  =  models.CharField(max_length=16,blank=True,verbose_name=u'区')
    
    receiver_address   =  models.CharField(max_length=128,blank=True,verbose_name=u'详细地址')
    receiver_zip       =  models.CharField(max_length=10,blank=True,verbose_name=u'邮编')
    receiver_mobile    =  models.CharField(max_length=24,db_index=True,blank=True,verbose_name=u'手机')
    receiver_phone     =  models.CharField(max_length=20,blank=True,verbose_name=u'电话')

    status = models.IntegerField(choices=TRADE_STATUS,default=TRADE_NO_CREATE_PAY,
                              db_index=True,blank=True,verbose_name=u'交易状态')

    class Meta:
        db_table = 'flashsale_trade'
        verbose_name=u'特卖/订单'
        verbose_name_plural = u'特卖/订单列表'

    def __unicode__(self):
        return '<%s,%s>'%(str(self.id),self.buyer_nick)
    


class SaleOrder(models.Model):
    
    TRADE_NO_CREATE_PAY = 0
    WAIT_BUYER_PAY = 1
    WAIT_SELLER_SEND_GOODS = 2
    WAIT_BUYER_CONFIRM_GOODS = 3
    TRADE_BUYER_SIGNED = 4
    TRADE_FINISHED = 5
    TRADE_CLOSED = 6
    TRADE_CLOSED_BY_TAOBAO = 7
    
    ORDER_STATUS = (
        (TRADE_NO_CREATE_PAY,u'订单创建'),
        (WAIT_BUYER_PAY,u'待付款'),
        (WAIT_SELLER_SEND_GOODS,u'待发货'),
        (WAIT_BUYER_CONFIRM_GOODS,u'待确认收货'),
        (TRADE_BUYER_SIGNED,u'货到付款签收'),
        (TRADE_FINISHED,u'交易成功'),
        (TRADE_CLOSED,u'退款交易关闭'),
        (TRADE_CLOSED_BY_TAOBAO,u'未付款关闭'),
    )

    id    = BigIntegerAutoField(primary_key=True)
    oid   = models.CharField(max_length=64,
                             verbose_name=u'原单ID')
    sale_trade = BigIntegerForeignKey(SaleTrade,
                                       related_name='sale_orders',
                                       verbose_name=u'所属订单')
    
    item_id  = models.CharField(max_length=64,blank=True,verbose_name=u'商品ID')
    title  =  models.CharField(max_length=128,blank=True,verbose_name=u'商品标题')
    price  = models.FloatField(default=0.0,verbose_name=u'单价')

    sku_id = models.CharField(max_length=20,blank=True,verbose_name=u'属性编码')
    num = models.IntegerField(null=True,default=0,verbose_name=u'商品数量')
    
    outer_id = models.CharField(max_length=64,blank=True,verbose_name=u'商品外部编码')
    outer_sku_id = models.CharField(max_length=20,blank=True,verbose_name=u'规格外部编码')
    
    total_fee    = models.FloatField(default=0.0,verbose_name=u'总费用')
    payment      = models.FloatField(default=0.0,verbose_name=u'实付款')

    sku_name = models.CharField(max_length=256,blank=True,
                                           verbose_name=u'购买规格')
    
    pic_path = models.CharField(max_length=512,blank=True,verbose_name=u'商品图片')
    
    created       =  models.DateTimeField(null=True,blank=True,verbose_name=u'创建日期')
    modified      = models.DateTimeField(null=True,blank=True,verbose_name=u'修改日期')
    pay_time      =  models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'付款日期')
    consign_time  =  models.DateTimeField(null=True,blank=True,verbose_name=u'发货日期')
    
    status = models.IntegerField(choices=ORDER_STATUS,default=TRADE_NO_CREATE_PAY,
                              db_index=True,blank=True,verbose_name=u'订单状态')

    class Meta:
        db_table = 'flashsale_order'
        unique_together = ("oid","sale_trade")
        verbose_name=u'特卖/订单明细'
        verbose_name_plural = u'特卖/订单明细列表'
        
    def __unicode__(self):
        return '<%s>'%(self.id)
        
    