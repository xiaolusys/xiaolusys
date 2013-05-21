#-*- coding:utf8 -*-
"""
淘宝分销平台模型:
FenxiaoProduct:为分销平台商品,
PurchaseOrder:分销平台售出订单，
SubPurchaseOrder:分销平台子订单，
"""
__author__ = 'meixqhi'
import json
import time
from auth.utils import parse_datetime
from django.db import models
from shopback.base.models import BaseModel
from shopback.users.models import User
from shopback.categorys.models import Category
from shopback.logistics.models import Logistics
from shopback import paramconfig as pcfg
from shopback.signals import merge_trade_signal
from auth import apis
import logging

logger = logging.getLogger('fenxiao.handler')



PURCHASE_ORDER_STATUS = (
    (pcfg.WAIT_BUYER_PAY,"等待付款"),
    (pcfg.WAIT_SELLER_SEND_GOODS,"已付款，待发货"),
    (pcfg.WAIT_BUYER_CONFIRM_GOODS,"已付款，已发货"),
    (pcfg.TRADE_FINISHED,"交易成功"),
    (pcfg.TRADE_CLOSED,"交易关闭"),
    (pcfg.WAIT_BUYER_CONFIRM_GOODS_ACOUNTED,"已付款（已分账），已发货"),
    (pcfg.WAIT_SELLER_SEND_GOODS_ACOUNTED,"已付款（已分账），待发货"),
) 

SUB_PURCHASE_ORDER_STATUS = (
    (pcfg.WAIT_BUYER_PAY,"等待付款"),
    (pcfg.WAIT_CONFIRM,"付款信息待确认"),
    (pcfg.WAIT_CONFIRM_WAIT_SEND_GOODS,"付款信息待确认，待发货"),
    (pcfg.WAIT_CONFIRM_SEND_GOODS,"付款信息待确认，已发货"),
    (pcfg.WAIT_CONFIRM_GOODS_CONFIRM,"付款信息待确认，已收货"),
    (pcfg.WAIT_SELLER_SEND_GOODS,"已付款，待发货"),
    (pcfg.WAIT_BUYER_CONFIRM_GOODS,"已付款，已发货"),
    (pcfg.CONFIRM_WAIT_SEND_GOODS,"付款信息已确认，待发货"),
    (pcfg.CONFIRM_SEND_GOODS,"付款信息已确认，已发货"),
    (pcfg.TRADE_REFUNDED,"已退款"),
    (pcfg.TRADE_REFUNDING,"退款中"),
    (pcfg.TRADE_FINISHED,"交易成功"),
    (pcfg.TRADE_CLOSED,"交易关闭"),
)

PAY_TYPE_CHOICES = (
    (pcfg.ALIPAY_SURETY_TYPE,'支付宝担保交易'),
    (pcfg.ALIPAY_CHAIN_TYPE,'分账交易'),
    (pcfg.TRANSFER_TYPE,'线下转账'),
    (pcfg.PREPAY_TYPE,'预存款'),
    (pcfg.IMMEDIATELY_TYPE,'即时到账'),
)

class FenxiaoProduct(models.Model):
    
    pid               = models.CharField(max_length=64,primary_key=True)
    name              = models.CharField(max_length=64,blank=True)
    productcat_id     = models.CharField(max_length=64,blank=True)
    
    user              = models.ForeignKey(User,null=True,related_name='fenxiao_products')
    category          = models.ForeignKey(Category,null=True,related_name='fenxiao_products')
    
    discount_id       = models.CharField(max_length=64,blank=True)
    trade_type        = models.CharField(max_length=7,blank=True)
    standard_price    = models.CharField(max_length=10,blank=True)
    upshelf_time      = models.DateTimeField(null=True)
    
    is_authz          = models.CharField(max_length=3,blank=True)
    properties        = models.TextField(max_length=1000,blank=True)
    
    property_alias    = models.TextField(max_length=1000,blank=True)
    input_properties  = models.TextField(max_length=1000,blank=True)
    description       = models.TextField(max_length=25000,blank=True)
    dealer_cost_price = models.CharField(max_length=10,blank=True)
    
    item_id           = models.CharField(max_length=64,blank=True)   
    pdus              = models.TextField(max_length=5000,blank=True)
    cost_price        = models.CharField(max_length=10,blank=True)
    retail_price_low  = models.CharField(max_length=10,blank=True)
    retail_price_high = models.CharField(max_length=10,blank=True)
    
    outer_id          = models.CharField(max_length=64,blank=True)
    quantity          = models.IntegerField(null=True)
    alarm_number      = models.IntegerField(null=True)
    pictures          = models.TextField(max_length=1000,blank=True)
    
    desc_path         = models.CharField(max_length=256,blank=True)
    prov              = models.CharField(max_length=16,blank=True)
    city              = models.CharField(max_length=16,blank=True)
    
    postage_id        = models.CharField(max_length=64,blank=True)
    postage_type      = models.CharField(max_length=10,blank=True)
    postage_ordinary  = models.CharField(max_length=10,blank=True)
    postage_fast      = models.CharField(max_length=10,blank=True)
    postage_ems       = models.CharField(max_length=10,blank=True)
    
    skus              = models.TextField(max_length=5000,blank=True)
    have_invoice      = models.BooleanField(default=False)
    have_guarantee    = models.BooleanField(default=False)
    
    items_count       = models.IntegerField(null=True)
    orders_count      = models.IntegerField(null=True)
    created           = models.DateTimeField(null=True)
    modified          = models.DateTimeField(null=True)
    
    status            = models.CharField(max_length=10,blank=True)
    class Meta:
        db_table = 'shop_fenxiao_product'

    def __unicode__(self):
        return str(self.pid)
    
    @classmethod
    def get_or_create(cls,user_id,pid):
        fenxiao_product,state = cls.objects.get_or_create(pid=pid)
        if state:
            try:
                response = apis.taobao_fenxiao_products_get(pids=pid,tb_user_id=user_id)
                if response['fenxiao_products_get_response']['total_results']>0:
                    fenxiao_product_dict = response['fenxiao_products_get_response']['products']['fenxiao_product'][0]
                    fenxiao_product = cls.save_fenxiao_product_dict(user_id,fenxiao_product_dict)
            except Exception,exc:
                logger.error('backend update fenxiao trade(pid:%s)error'%str(pid),exc_info=True)
        return fenxiao_product
    
    @classmethod
    def save_fenxiao_product_dict(cls,user_id,fenxiao_product_dict):
        
        fenxiao_product,state = cls.objects.get_or_create(pid=fenxiao_product_dict['pid'])
        for k,v in fenxiao_product_dict.iteritems():
            hasattr(fenxiao_product,k) and setattr(fenxiao_product,k,v)
        fenxiao_product.user = User.objects.get(visitor_id=user_id)
        fenxiao_product.category = Category.get_or_create(user_id,fenxiao_product_dict['category_id'])
        fenxiao_product.pdus = json.dumps(fenxiao_product_dict.get('pdus',None))
        fenxiao_product.skus = json.dumps(fenxiao_product_dict.get('skus',None))
        fenxiao_product.save()
        return fenxiao_product
    
    


class PurchaseOrder(models.Model):

    fenxiao_id = models.CharField(max_length=64,primary_key=True)
    id         = models.CharField(max_length=64,db_index=True,blank=True)

    user       = models.ForeignKey(User,null=True,related_name='purchases')

    seller_id          = models.CharField(max_length=64,blank=True)
    supplier_username  = models.CharField(max_length=64,blank=True)
    supplier_memo      = models.TextField(max_length=1000,blank=True)
    supplier_from      = models.CharField(max_length=20,blank=True)

    distributor_from   = models.CharField(max_length=20,blank=True)
    distributor_username    = models.CharField(max_length=32,blank=True)
    distributor_payment     = models.CharField(max_length=10,blank=True)

    logistics_id       = models.CharField(db_index=True,max_length=64,blank=True)
    logistics_company_name  = models.CharField(max_length=64,blank=True)
    consign_time       = models.DateTimeField(db_index=True,null=True,blank=True)

    pay_time   = models.DateTimeField(db_index=True,null=True,blank=True)
    pay_type   = models.CharField(max_length=32,choices=PAY_TYPE_CHOICES,blank=True)

    post_fee   = models.CharField(max_length=10,blank=True)
    total_fee  = models.CharField(max_length=10,blank=True)

    shipping   = models.CharField(max_length=10,blank=True)
    trade_type = models.CharField(max_length=10,blank=True)
    memo       = models.TextField(max_length=1000,blank=True)
    supplier_flag  = models.IntegerField(null=True)
    
    created    = models.DateTimeField(null=True,blank=True)
    modified   = models.DateTimeField(null=True,blank=True)
    
    tc_order_id = models.CharField(max_length=64,blank=True)
    alipay_no   = models.CharField(max_length=64,blank=True)
    status     = models.CharField(max_length=32,choices=PURCHASE_ORDER_STATUS,blank=True)

    class Meta:
        db_table = 'shop_fenxiao_purchaseorder'

    def __unicode__(self):
        return '<%s,%s>'%(self.fenxiao_id,self.supplier_username)
    
        
    @classmethod
    def save_order_through_dict(cls,seller_id,purchase_order_dict):
        
        purchase_order,state = cls.objects.get_or_create(fenxiao_id=purchase_order_dict['fenxiao_id'])
        purchase_order.user  =  User.objects.get(visitor_id=seller_id)
        purchase_order.seller_id  =  seller_id
        sub_purchase_orders  = purchase_order_dict.pop('sub_purchase_orders')   
        for k,v in purchase_order_dict.iteritems():
            hasattr(purchase_order,k) and setattr(purchase_order,k,v)
	
        purchase_order.created  = parse_datetime(purchase_order_dict['created']) \
            if purchase_order_dict.get('created',None) else None
        purchase_order.pay_time = parse_datetime(purchase_order_dict['pay_time']) \
            if purchase_order_dict.get('pay_time',None) else None
        purchase_order.modified = parse_datetime(purchase_order_dict['modified']) \
            if purchase_order_dict.get('modified',None) else None
        purchase_order.consign_time = parse_datetime(purchase_order_dict['consign_time']) \
            if purchase_order_dict.get('consign_time',None) else None
        
        purchase_order.save()
        
        for sub_order in  sub_purchase_orders['sub_purchase_order']:
            sub_purchase_order,state= SubPurchaseOrder.objects.get_or_create(fenxiao_id=sub_order['fenxiao_id'])

            for k,v in sub_order.iteritems():
                hasattr(sub_purchase_order,k) and setattr(sub_purchase_order,k,v)
            sub_purchase_order.purchase_order  = purchase_order
            sub_purchase_order.fenxiao_product = FenxiaoProduct.get_or_create(seller_id,sub_order['item_id'])
            sub_purchase_order.created  = parse_datetime(sub_order['created']) \
                if sub_order.get('created',None) else None
            sub_purchase_order.save()
           
        merge_trade_signal.send(sender=PurchaseOrder,trade=purchase_order)
        return purchase_order
            
        

class SubPurchaseOrder(models.Model):
    fenxiao_id       = models.CharField(max_length=64,primary_key=True)
    id               = models.CharField(max_length=64,blank=True)
    
    purchase_order   = models.ForeignKey(PurchaseOrder,null=True,related_name='sub_purchase_orders')
    
    sku_id           = models.CharField(max_length=64,blank=True)
    tc_order_id      = models.CharField(max_length=64,blank=True)
    
    fenxiao_product  = models.ForeignKey(FenxiaoProduct,null=True,related_name='sub_purchase_orders')
    item_id          = models.CharField(max_length=64,blank=True)
    title            = models.CharField(max_length=64,blank=True)
    
    num              = models.IntegerField(null=True)
    price            = models.CharField(max_length=10,blank=True)
    
    total_fee        = models.CharField(max_length=10,blank=True)
    distributor_payment  = models.CharField(max_length=10,blank=True)
    buyer_payment    = models.CharField(max_length=10,blank=True)
    
    order_200_status = models.CharField(max_length=32,blank=True)
    auction_price    = models.CharField(max_length=10,blank=True)
    
    old_sku_properties  = models.TextField(max_length=1000,blank=True)
    
    item_outer_id    = models.CharField(max_length=64,blank=True)
    sku_outer_id     = models.CharField(max_length=64,blank=True)
    sku_properties   = models.TextField(max_length=1000,blank=True)
    
    snapshot_url     = models.CharField(max_length=256,blank=True)
    created          = models.DateTimeField(null=True)
    
    refund_fee       = models.CharField(max_length=10,blank=True)
    status           = models.CharField(max_length=32,choices=SUB_PURCHASE_ORDER_STATUS,blank=True)
    
    class Meta:
        db_table = 'shop_fenxiao_subpurchaseorder'

    def __unicode__(self):
        return str(self.fenxiao_id)  
    
    @property
    def properties_values(self):
        sku_properties = self.old_sku_properties or self.sku_properties
        properties_list = sku_properties.split('，'.decode('utf8'))
        value_list = []
        for properties in properties_list:
            values = properties.split('：'.decode('utf8'))
            value_list.append( values[1] if len(values)==2 else properties)
        return ' '.join(value_list)
        
  

    
    
    
