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

#不需客服介入1; 需要客服介入2; 客服已经介入3; 客服初审完成 4; 客服主管复审失败5; 客服处理完成6;
CS_STATUS_CHOICES = (
    (1,'不需客服介入'),
    (2,'需要客服介入'),
    (3,'客服已经介入'),
    (4,'客服初审完成'),
    (5,'客服主管复审失败'),
    (6,'客服处理完成'),
)

class Refund(models.Model):

    refund_id    = BigIntegerAutoField(primary_key=True,verbose_name='退款ID')
    tid          = models.BigIntegerField(null=True,db_index=True,verbose_name='交易ID')

    title        = models.CharField(max_length=64,blank=True,verbose_name='出售标题')
    num_iid      = models.BigIntegerField(null=True,verbose_name='商品ID')

    user         = models.ForeignKey(User,null=True,related_name='refunds',verbose_name='店铺')
    seller_id    = models.CharField(max_length=64,blank=True,verbose_name='卖家ID')
    buyer_nick   = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='买家昵称')
    seller_nick  = models.CharField(max_length=64,blank=True,verbose_name='卖家昵称')
    
    mobile = models.CharField(max_length=20,db_index=True,blank=True,verbose_name='手机')
    phone  = models.CharField(max_length=20,db_index=True,blank=True,verbose_name='固话')
    
    total_fee    = models.CharField(max_length=10,blank=True,verbose_name='总费用')
    refund_fee   = models.CharField(max_length=10,blank=True,verbose_name='退款费用')
    payment      = models.CharField(max_length=10,blank=True,verbose_name='实付')

    created   = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='创建日期')
    modified  = models.DateTimeField(db_index=True,null=True,blank=True,verbose_name='修改日期')

    oid       = models.CharField(db_index=True,max_length=64,blank=True,verbose_name='订单ID')
    company_name = models.CharField(max_length=64,blank=True,verbose_name='快递公司')
    sid       = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='快递单号')

    reason    = models.TextField(max_length=200,blank=True,verbose_name='退款原因')
    desc      = models.TextField(max_length=1000,blank=True,verbose_name='描述')
    has_good_return = models.BooleanField(default=False,verbose_name='是否退货')

    good_status  = models.CharField(max_length=32,blank=True,choices=GOOD_STATUS_CHOICES,verbose_name='退货商品状态')
    order_status = models.CharField(max_length=32,blank=True,choices=ORDER_STATUS_CHOICES,verbose_name='订单状态')
    cs_status    = models.IntegerField(default=1,choices=CS_STATUS_CHOICES,verbose_name='天猫客服介入状态')
    status       = models.CharField(max_length=32,blank=True,choices=REFUND_STATUS,verbose_name='退款状态')

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

        self.user   = User.objects.get(visitor_id=seller_id)
        from shopback.trades.models import MergeTrade
        try:
            merge_trade = MergeTrade.objects.get(tid=refund['tid'])
        except:
            pass
        
        self.mobile = merge_trade and merge_trade.receiver_mobile or ''
        self.phone  = merge_trade and merge_trade.receiver_phone  or ''
        
        for k,v in refund.iteritems():
            hasattr(self,k) and setattr(self,k,v)
            
        self.created  = parse_datetime(refund['created']) \
            if refund.get('created',None) else None
        self.modified = parse_datetime(refund['modified']) \
            if refund.get('modified',None) else None
        
        self.save()
        

class RefundProduct(models.Model):
    
    buyer_nick   = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='买家昵称')
    buyer_mobile = models.CharField(max_length=22,db_index=True,blank=True,verbose_name='手机')
    buyer_phone  = models.CharField(max_length=22,db_index=True,blank=True,verbose_name='固话')
    trade_id     = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='淘宝订单编号')
    out_sid      = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='物流单号')
    company      = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='物流名称')
    
    outer_id     = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='商品编码')
    outer_sku_id = models.CharField(max_length=64,db_index=True,blank=True,verbose_name='规格编码')
    num          = models.IntegerField(default=0,verbose_name='数量')
    title        = models.CharField(max_length=64,blank=True,verbose_name='商品名称')
    property     = models.CharField(max_length=64,blank=True,verbose_name='规格名称')
    
    can_reuse    = models.BooleanField(default=False,verbose_name='能否二次销售')
    is_finish    = models.BooleanField(default=False,verbose_name='处理完成')
    
    created      = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='创建时间')
    modified     = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='修改时间')
    
    memo         = models.TextField(max_length=1000,blank=True,verbose_name='备注')
    
    class Meta:
        db_table = 'shop_refunds_product'
        verbose_name = u'退货商品'
        verbose_name_plural = u'退货商品列表'

    def __unicode__(self):
        info_list = [self.buyer_nick,self.buyer_mobile,self.buyer_phone,self.trade_id,self.out_sid,self.company]
        info_string = '-'.join([ s for s in info_list if s])    
        return '<%s,%s,%s>'%(info_string,self.outer_id,self.outer_sku_id)
    
    