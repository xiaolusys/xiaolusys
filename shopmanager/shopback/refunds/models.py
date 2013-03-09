#-*- coding:utf8 -*-
__author__ = 'meixqhi'
import json
import time
from auth.utils import parse_datetime
from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField,BigIntegerForeignKey
from shopback import paramconfig as pcfg
from shopback.users.models import User
from auth import apis
import logging

logger = logging.getLogger('refunds.handler')

REFUND_STATUS = (
    (pcfg.NO_REFUND,'没有退款'),
    (pcfg.REFUND_WAIT_SELLER_AGREE,'买家已经申请退款'),
    (pcfg.REFUND_WAIT_RETURN_GOODS,'卖家已经同意退款'),
    (pcfg.REFUND_CONFIRM_GOODS,'买家已经退货'),
    (pcfg.REFUND_REFUSE_BUYER,'卖家拒绝退款'),
    (pcfg.REFUND_CLOSED,'退款关闭'),
    (pcfg.REFUND_SUCCESS,'退款成功'),
)

GOOD_STATUS_CHOICES = (
    ('BUYER_NOT_RECEIVED','买家未收到货'),
    ('BUYER_RECEIVED','买家已收到货'),
    ('BUYER_RETURNED_GOODS','买家已退货'),
)

ORDER_STATUS_CHOICES = (
    (pcfg.TRADE_NO_CREATE_PAY,'没有创建支付宝交易'),
    (pcfg.WAIT_BUYER_PAY,'等待买家付款'),
    (pcfg.WAIT_SELLER_SEND_GOODS,'等待卖家发货'),
    (pcfg.WAIT_BUYER_CONFIRM_GOODS,'等待买家确认收货'),
    (pcfg.TRADE_BUYER_SIGNED,'已签收,货到付款专用'),
    (pcfg.TRADE_FINISHED,'交易成功'),
    (pcfg.TRADE_CLOSED,'退款成功交易自动关闭'),
    (pcfg.TRADE_CLOSED_BY_TAOBAO,'付款前关闭交易'),
)

class Refund(models.Model):

    refund_id    = BigIntegerAutoField(primary_key=True,verbose_name='退款ID')
    tid          = models.BigIntegerField(null=True,verbose_name='交易ID')

    title        = models.CharField(max_length=64,blank=True,verbose_name='出售标题')
    num_iid      = models.BigIntegerField(null=True,verbose_name='商品ID')

    user         = models.ForeignKey(User,null=True,related_name='refunds',verbose_name='店铺')
    seller_id    = models.CharField(max_length=64,blank=True,verbose_name='卖家ID')
    buyer_nick   = models.CharField(max_length=64,blank=True,verbose_name='买家昵称')
    seller_nick  = models.CharField(max_length=64,blank=True,verbose_name='卖家昵称')

    total_fee    = models.CharField(max_length=10,blank=True,verbose_name='总费用')
    refund_fee   = models.CharField(max_length=10,blank=True,verbose_name='退款费用')
    payment      = models.CharField(max_length=10,blank=True,verbose_name='实付')

    created   = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='创建日期')
    modified  = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='修改日期')

    oid       = models.CharField(db_index=True,max_length=64,blank=True,verbose_name='订单ID')
    company_name = models.CharField(max_length=64,blank=True,verbose_name='快递公司')
    sid       = models.CharField(max_length=64,blank=True,verbose_name='快递单号')

    reason    = models.TextField(max_length=200,blank=True,verbose_name='退款原因')
    desc      = models.TextField(max_length=1000,blank=True,verbose_name='描述')
    has_good_return = models.BooleanField(default=False,verbose_name='是否退货')

    good_status  = models.CharField(max_length=32,blank=True,choices=GOOD_STATUS_CHOICES,verbose_name='退货商品状态')
    order_status = models.CharField(max_length=32,blank=True,choices=ORDER_STATUS_CHOICES,verbose_name='订单状态')
    status       = models.CharField(max_length=32,blank=True,choices=REFUND_STATUS,verbose_name='退款ID')

    class Meta:
        db_table = 'shop_refunds_refund'
        verbose_name = u'退款单'
        verbose_name_plural = u'退款单列表'

    def __unicode__(self):
        return '<%s,%s,%s>'%(str(self.refund_id),self.buyer_nick,self.refund_fee)

    @classmethod
    def get_or_create(cls,user_id,refund_id,force_update=False):
        refund,state = cls.objects.get_or_create(refund_id=refund_id)
        if state or force_update:
            try:
                response = apis.taobao_refund_get(refund_id,tb_user_id=user_id)
                refund_dict = response['refund_get_response']['refund']
                refund.save_refund_through_dict(user_id,refund_dict)
            except Exception,exc:
                logger.error(exc.message,exc_info=True)
        return refund
                
    def save_refund_through_dict(self,seller_id,refund):

        self.user  = User.objects.get(visitor_id=seller_id)
        for k,v in refund.iteritems():
            hasattr(self,k) and setattr(self,k,v)

        self.created  = parse_datetime(refund['created']) \
            if refund.get('created',None) else None
        self.modified = parse_datetime(refund['modified']) \
            if refund.get('modified',None) else None

        self.save()
        
