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
from .models_user import Register,Customer
from .models_addr import District,UserAddress
from .models_custom import Productdetail

import uuid

def genUUID():
    return str(uuid.uuid1(clock_seq=True))

class SaleTrade(models.Model):
    
    WX_PUB     = 'wx_pub'
    ALIPAY_WAP = 'alipay_wap'
    UPMP_WAP   = 'upmp_wap'
    
    CHANNEL_CHOICES = (
        (WX_PUB,u'微支付'),
        (ALIPAY_WAP,u'支付宝'),
        (UPMP_WAP,u'银联'),
    )
    
    PREPAY  = 0
    POSTPAY = 1
    
    TRADE_TYPE_CHOICES = (
        (PREPAY,u"在线支付"),
        (POSTPAY,"货到付款"),
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
    
    tid   = models.CharField(max_length=40,unique=True,verbose_name=u'原单ID')  
    buyer_id   = models.BigIntegerField(null=False,db_index=True,verbose_name=u'买家ID')
    buyer_nick  = models.CharField(max_length=64,blank=True,verbose_name=u'买家昵称')
    
    channel     = models.CharField(max_length=16,choices=CHANNEL_CHOICES,blank=True,verbose_name=u'付款类型')
    
    payment    =   models.FloatField(default=0.0,verbose_name=u'实付款')
    post_fee   =   models.FloatField(default=0.0,verbose_name=u'物流费用')
    total_fee  =   models.FloatField(default=0.0,verbose_name=u'总费用')
    
    buyer_message = models.TextField(max_length=1000,blank=True,verbose_name=u'买家留言')
    seller_memo   = models.TextField(max_length=1000,blank=True,verbose_name=u'卖家备注')
    
    created      = models.DateTimeField(null=True,auto_now_add=True,blank=True,verbose_name=u'生成日期')
    pay_time     = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'付款日期')
    modified     = models.DateTimeField(null=True,auto_now=True,blank=True,verbose_name=u'修改日期')
    consign_time = models.DateTimeField(null=True,blank=True,verbose_name=u'发货日期')
    
    trade_type = models.IntegerField(choices=TRADE_TYPE_CHOICES,default=PREPAY,verbose_name=u'订单类型')
    
    out_sid         = models.CharField(max_length=64,blank=True,verbose_name=u'物流编号')
    logistics_company  = models.ForeignKey(LogisticsCompany,null=True,
                                           blank=True,verbose_name=u'物流公司')
    receiver_name    =  models.CharField(max_length=25,
                                         blank=True,verbose_name=u'收货人姓名')
    receiver_state   =  models.CharField(max_length=16,blank=True,verbose_name=u'省')
    receiver_city    =  models.CharField(max_length=16,blank=True,verbose_name=u'市')
    receiver_district  =  models.CharField(max_length=16,blank=True,verbose_name=u'区')
    
    receiver_address   =  models.CharField(max_length=128,blank=True,verbose_name=u'详细地址')
    receiver_zip       =  models.CharField(max_length=10,blank=True,verbose_name=u'邮编')
    receiver_mobile    =  models.CharField(max_length=11,db_index=True,blank=True,verbose_name=u'手机')
    receiver_phone     =  models.CharField(max_length=20,blank=True,verbose_name=u'电话')

    openid  = models.CharField(max_length=40,blank=True,verbose_name=u'微信用户ID')

    status  = models.IntegerField(choices=TRADE_STATUS,default=TRADE_NO_CREATE_PAY,
                              db_index=True,blank=True,verbose_name=u'交易状态')

    class Meta:
        db_table = 'flashsale_trade'
        verbose_name=u'特卖/订单'
        verbose_name_plural = u'特卖/订单列表'

    def __unicode__(self):
        return '<%s,%s>'%(str(self.id),self.buyer_nick)
    
    @property
    def body_describe(self):
        subc = ''
        for order in self.sale_orders.all():
            subc += order.title
        return subc
    
    @classmethod
    def mapTradeStatus(cls,index):
        from shopback.trades.models import MergeTrade
        status_list = MergeTrade.TAOBAO_TRADE_STATUS
        return status_list[index][0]

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
    oid   = models.CharField(max_length=40,unique=True,verbose_name=u'原单ID')
    sale_trade = BigIntegerForeignKey(SaleTrade,related_name='sale_orders',
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
    
    created       =  models.DateTimeField(null=True,auto_now_add=True,blank=True,verbose_name=u'创建日期')
    modified      = models.DateTimeField(null=True,auto_now=True,blank=True,verbose_name=u'修改日期')
    pay_time      =  models.DateTimeField(db_index=True,null=True,blank=True,verbose_name=u'付款日期')
    consign_time  =  models.DateTimeField(null=True,blank=True,verbose_name=u'发货日期')
    
    status = models.IntegerField(choices=ORDER_STATUS,default=TRADE_NO_CREATE_PAY,
                              db_index=True,blank=True,verbose_name=u'订单状态')

    class Meta:
        db_table = 'flashsale_order'
        verbose_name=u'特卖/订单明细'
        verbose_name_plural = u'特卖/订单明细列表'
        
    def __unicode__(self):
        return '<%s>'%(self.id)


class SaleRefund(models.Model):
    
    id           = BigIntegerAutoField(primary_key=True,verbose_name='ID')
    refund_id    = models.CharField(max_length=32,
                                    default=lambda:'RF%d'%int(time.time()*10**2),
                                    verbose_name='退款单ID')
    tid          = models.CharField(max_length=32,blank=True,verbose_name='交易ID')
    
    item_id      = models.BigIntegerField(null=True,default=0,verbose_name='商品ID')
    title        = models.CharField(max_length=64,blank=True,verbose_name='出售标题')

    buyer_nick   = models.CharField(max_length=64,blank=True,verbose_name='买家昵称')
    mobile = models.CharField(max_length=20,db_index=True,blank=True,verbose_name='手机')
    phone  = models.CharField(max_length=20,db_index=True,blank=True,verbose_name='固话')
    
    total_fee    = models.CharField(max_length=10,blank=True,verbose_name='总费用')
    refund_fee   = models.CharField(max_length=10,blank=True,verbose_name='退款费用')
    payment      = models.CharField(max_length=10,blank=True,verbose_name='实付')

    created   = models.DateTimeField(db_index=True,null=True,auto_now_add=True,verbose_name='创建日期')
    modified  = models.DateTimeField(db_index=True,null=True,auto_now=True,verbose_name='修改日期')

    oid       = models.CharField(db_index=True,max_length=32,blank=True,verbose_name='订单ID')
    sku_name  = models.CharField(max_length=64,blank=True,verbose_name='规格标题')
    
    company_name = models.CharField(max_length=64,blank=True,verbose_name='快递公司')
    sid       = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='快递单号')

    reason    = models.TextField(max_length=200,blank=True,verbose_name='退款原因')
    desc      = models.TextField(max_length=1000,blank=True,verbose_name='描述')
    has_good_return = models.BooleanField(default=False,verbose_name='是否退货')
    
    is_reissue   = models.BooleanField(default=False,verbose_name='已处理')
    
    good_status  = models.CharField(max_length=32,blank=True,verbose_name='退货商品状态')
    order_status = models.CharField(max_length=32,blank=True,verbose_name='订单状态')

    status       = models.CharField(max_length=32,blank=True,verbose_name='退款状态')

    class Meta:
        db_table = 'flashsale_refund'
        verbose_name=u'特卖/退款单'
        verbose_name_plural = u'特卖/退款单列表'
        
    def __unicode__(self):
        return '<%s>'%(self.id)


class TradeCharge(models.Model):
    
    order_no    = models.BigIntegerField(verbose_name=u'订单ID')
    charge      = models.CharField(max_length=28,verbose_name=u'CH-ID')
    
    paid        = models.BooleanField(db_index=True,default=False,verbose_name=u'付款')
    refunded    = models.BooleanField(db_index=True,default=False,verbose_name=u'退款')
    
    channel     = models.CharField(max_length=16,blank=True,verbose_name=u'支付方式')
    amount      = models.CharField(max_length=10,blank=True,verbose_name=u'付款金额')
    currency    = models.CharField(max_length=8,blank=True,verbose_name=u'币种')
    
    transaction_no  = models.CharField(max_length=28,blank=True,verbose_name=u'事务NO')
    amount_refunded = models.CharField(max_length=16,blank=True,verbose_name=u'退款金额')
    
    failure_code    = models.CharField(max_length=16,blank=True,verbose_name=u'错误编码')
    failure_msg     = models.CharField(max_length=16,blank=True,verbose_name=u'错误信息')
    
    time_paid       = models.DateTimeField(null=True,blank=True,db_index=True,verbose_name=u'付款时间')
    time_expire     = models.DateTimeField(null=True,blank=True,db_index=True,verbose_name=u'失效时间')
    
    class Meta:
        db_table = 'flashsale_trade_charge'
        unique_together = ("order_no","charge")
        verbose_name=u'特卖支付/交易'
        verbose_name_plural = u'特卖支付/交易列表'
        
    def __unicode__(self):
        return '<%s>'%(self.id)
    
    