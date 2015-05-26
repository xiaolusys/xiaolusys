#-*- coding:utf-8 -*-
import time
import datetime
from django.db import models
from django.db.models import Q,Sum
from django.db.models.signals import post_save
from django.db import IntegrityError, transaction

from shopback import paramconfig as pcfg
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from .options import uniqid

class SaleRefund(models.Model):
    
    NO_REFUND = 0
    REFUND_CLOSED = 1
    REFUND_REFUSE_BUYER = 2
    REFUND_WAIT_SELLER_AGREE = 3
    REFUND_WAIT_RETURN_GOODS = 4
    REFUND_CONFIRM_GOODS = 5
    REFUND_APPROVE = 6
    REFUND_SUCCESS = 7
    
    
    REFUND_STATUS = (
        (NO_REFUND,'没有退款'),
        (REFUND_WAIT_SELLER_AGREE,'买家已经申请退款'),
        (REFUND_WAIT_RETURN_GOODS,'卖家已经同意退款'),
        (REFUND_CONFIRM_GOODS,'买家已经退货'),
        (REFUND_REFUSE_BUYER,'卖家拒绝退款'),
        (REFUND_APPROVE,'确认退款，等待返款'),
        (REFUND_CLOSED,'退款关闭'),
        (REFUND_SUCCESS,'退款成功'),
    )
    
    REFUND_STATUS_MAP = (
        (NO_REFUND,pcfg.NO_REFUND),
        (REFUND_WAIT_SELLER_AGREE,pcfg.REFUND_WAIT_SELLER_AGREE),
        (REFUND_WAIT_RETURN_GOODS,pcfg.REFUND_WAIT_RETURN_GOODS),
        (REFUND_CONFIRM_GOODS,pcfg.REFUND_CONFIRM_GOODS),
        (REFUND_REFUSE_BUYER,pcfg.REFUND_REFUSE_BUYER),
        (REFUND_APPROVE,pcfg.REFUND_SUCCESS),
        (REFUND_CLOSED,pcfg.REFUND_CLOSED),
        (REFUND_SUCCESS,pcfg.REFUND_SUCCESS)
    )
    
    BUYER_NOT_RECEIVED = 0
    BUYER_RECEIVED = 1
    BUYER_RETURNED_GOODS = 2
    
    GOOD_STATUS_CHOICES = (
        (BUYER_NOT_RECEIVED,'买家未收到货'),
        (BUYER_RECEIVED,'买家已收到货'),
        (BUYER_RETURNED_GOODS,'买家已退货'),
    )
    
    id           = BigIntegerAutoField(primary_key=True,verbose_name='ID')
    refund_no    = models.CharField(max_length=32,unique=True,
                                    default=lambda:uniqid('RF%s'%(datetime.datetime.now().strftime('%y%m%d'))),
                                    verbose_name='退款编号')
    trade_id     = models.IntegerField(verbose_name='交易ID')
    order_id     = models.IntegerField(verbose_name='订单ID')
    
    refund_id   = models.CharField(max_length=28,blank=True,db_index=True,verbose_name=u'P++退款编号')
    charge      = models.CharField(max_length=28,blank=True,db_index=True,verbose_name=u'P++支付编号')
    
    item_id      = models.BigIntegerField(null=True,default=0,verbose_name='商品ID')
    title        = models.CharField(max_length=64,blank=True,verbose_name='出售标题')
    
    sku_id       = models.BigIntegerField(null=True,default=0,verbose_name='规格ID')
    sku_name     = models.CharField(max_length=64,blank=True,verbose_name='规格标题')
    
    refund_num   = models.IntegerField(default=0,verbose_name='退货数量')
    
    buyer_nick   = models.CharField(max_length=64,blank=True,verbose_name='买家昵称')
    mobile = models.CharField(max_length=20,db_index=True,blank=True,verbose_name='手机')
    phone  = models.CharField(max_length=20,blank=True,verbose_name='固话')
    
    total_fee    = models.FloatField(default=0.0,verbose_name='总费用')
    payment      = models.FloatField(default=0.0,verbose_name='实付')
    refund_fee   = models.FloatField(default=0.0,verbose_name='退款费用')
    
    created   = models.DateTimeField(db_index=True,auto_now_add=True,verbose_name='创建日期')
    modified  = models.DateTimeField(auto_now=True,verbose_name='修改日期')

    company_name = models.CharField(max_length=64,blank=True,verbose_name='退回快递公司')
    sid       = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='退回快递单号')

    reason    = models.TextField(max_length=200,blank=True,verbose_name='退款原因')
    desc      = models.TextField(max_length=1000,blank=True,verbose_name='描述')
    feedback  = models.TextField(max_length=1000,blank=True,verbose_name='审核意见')      
    
    has_good_return = models.BooleanField(default=False,verbose_name='是否退货')
    has_good_change = models.BooleanField(default=False,verbose_name='是否换货')
    
    good_status  = models.IntegerField(db_index=True,choices=GOOD_STATUS_CHOICES,
                                    default=BUYER_RECEIVED,blank=True,verbose_name='退货商品状态')

    status       = models.IntegerField(db_index=True,choices=REFUND_STATUS,
                                    default=REFUND_WAIT_SELLER_AGREE,blank=True,verbose_name='退款状态')

    class Meta:
        db_table = 'flashsale_refund'
        unique_together = ("trade_id","order_id")
        verbose_name=u'特卖/退款单'
        verbose_name_plural = u'特卖/退款单列表'
        
    def __unicode__(self):
        return '<%s>'%(self.id)
    
    def refund_desc(self):
        return u'退款不退货(oid:%s),%s'%(self.order_id,self.reason)
    
    def refund_Confirm(self):
        
        self.status = SaleRefund.REFUND_SUCCESS
        self.save()
        
        from flashsale.pay.models import SaleOrder,SaleTrade
        
        sorder = SaleOrder.objects.get(id=self.order_id)
        sorder.refund_status = SaleRefund.REFUND_SUCCESS
        if sorder.sale_trade.status == SaleTrade.WAIT_SELLER_SEND_GOODS:
            sorder.status = SaleTrade.TRADE_CLOSED
        sorder.save()
        
        strade = sorder.sale_trade
        if strade.normal_orders.count() == 0:
            strade.status = SaleTrade.TRADE_CLOSED
            strade.save()
    


    
    