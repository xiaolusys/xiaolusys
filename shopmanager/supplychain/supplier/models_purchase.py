#-*- coding:utf8 -*-
import os
import datetime
from django.db import models
from django.db.models.signals import post_save,post_delete
from django.db.models import Q,Sum,F
from django.conf import settings
from django.db import IntegrityError, transaction
from shopback import paramconfig as pcfg
from shopback.archives.models import Supplier,PurchaseType,Deposite
from shopback.categorys.models import ProductCategory
from shopback.items.models import Product,ProductSku
from shopback.monitor.models import SystemConfig
from common.utils import format_date,update_model_fields

FINANCIAL_FIXED = 4

PURCHASE_STATUS = (
    (pcfg.PURCHASE_DRAFT,'草稿'),
    (pcfg.PURCHASE_APPROVAL,'审核'),
    (pcfg.PURCHASE_FINISH,'完成'),
    (pcfg.PURCHASE_INVALID,'作废')
)


PURCHASE_ARRIVAL_STATUS = (
    (pcfg.PD_UNARRIVAL,'未到货'),
    (pcfg.PD_PARTARRIVAL,'部分到货'),
    (pcfg.PD_FULLARRIVAL,'全部到货')
)

PURCHASE_STORAGE_STATUS = (
    (pcfg.PURCHASE_DRAFT,'草稿'),
    (pcfg.PURCHASE_APPROVAL,'审核'),
    (pcfg.PURCHASE_FINISH,'完成'),
    (pcfg.PURCHASE_INVALID,'作废')
)

PURCHASE_PAYMENT_TYPE = (
    (pcfg.PC_COD_TYPE,'货到付款'),
    (pcfg.PC_PREPAID_TYPE,'预付款'),
    (pcfg.PC_POD_TYPE,'付款提货'),
    (pcfg.PC_OTHER_TYPE,'其它')
)

PRODUCT_STATUS = (
    (pcfg.NORMAL,'有效'),
    (pcfg.DELETE,'作废')
)

PAYMENT_STATUS = (
    (pcfg.PP_WAIT_APPLY,'未申请'),           
    (pcfg.PP_WAIT_PAYMENT,'待付款'),
    (pcfg.PP_HAS_PAYMENT,'已付款'),
    (pcfg.PP_INVALID,'已作废')
)

class Purchase(models.Model):
    """ 采购合同 """
    
    origin_no    = models.CharField(max_length=32,unique=True,verbose_name='原合同号')
    
    supplier     = models.ForeignKey(Supplier,null=True,blank=True,related_name='purchases',verbose_name='供应商')
    deposite     = models.ForeignKey(Deposite,null=True,blank=True,related_name='purchases',verbose_name='仓库')
    purchase_type = models.ForeignKey(PurchaseType,null=True,blank=True,related_name='purchases',verbose_name='采购类型')
    
    forecast_date = models.DateField(null=True,blank=True,verbose_name='预测到货日期')
    post_date     = models.DateField(null=True,blank=True,verbose_name='发货日期')
    
    created      = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='创建日期')
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='修改日期')
    
    purchase_num = models.IntegerField(null=True,default=0,verbose_name='采购数量')
    storage_num  = models.IntegerField(null=True,default=0,verbose_name='已入库数')
    
    total_fee    = models.FloatField(default=0.0,verbose_name='总费用')
    prepay       = models.FloatField(default=0.0,verbose_name='预付款')
    payment      = models.FloatField(default=0.0,verbose_name='已付款')
    
    receiver_name = models.CharField(max_length=32,blank=True,verbose_name='收货人')
    
    creator      = models.CharField(max_length=32,null=True,blank=True,verbose_name='创建人')
    operator     = models.CharField(max_length=32,null=True,blank=True,verbose_name='操作人')
    
    status       = models.CharField(max_length=32,db_index=True,choices=PURCHASE_STATUS,
                                    default=pcfg.PURCHASE_DRAFT,verbose_name='订单状态')
    
    arrival_status    = models.CharField(max_length=20,db_index=True,choices=PURCHASE_ARRIVAL_STATUS,
                                    default=pcfg.PD_UNARRIVAL,verbose_name='到货状态')
    
    extra_name   = models.CharField(max_length=256,blank=True,verbose_name='标题')
    extra_info   = models.TextField(blank=True,verbose_name='备注')
    
    prepay_cent  = models.FloatField(default=0.0,verbose_name='预付比例')
    
    class Meta:
        db_table = 'supply_purchase'
        verbose_name = u'采购单'
        verbose_name_plural = u'采购单列表'
        permissions = [
                       ("can_purchase_check", u"审批采购合同"),
                       ("can_purchase_confirm", u"确认采购完成"),
                       ]

    def __unicode__(self):
        return '<%s,%s,%s>'%(str(self.id or ''),self.origin_no,self.extra_name)
    
    @property
    def effect_purchase_items(self):
        return self.purchase_items.filter(status=pcfg.NORMAL)
    
    @property
    def unfinish_purchase_items(self):
        return self.effect_purchase_items.filter(arrival_status__in=(pcfg.PD_UNARRIVAL,pcfg.PD_PARTARRIVAL))
        
    @property
    def uncompletepay_item(self):
        uncpay_items = []
        for item in self.effect_purchase_items:
            afford_payment = item.price*item.storage_num
            if round(item.payment,1) < round(afford_payment,1):
                uncpay_items.append(item)
        return uncpay_items
        
    @property
    def total_unpay_fee(self):
        unpay_fee = 0
        for item in self.effect_purchase_items:
            unpay_fee += item.unpay_fee
            
        if unpay_fee<0:
            return 0
        return round(unpay_fee,FINANCIAL_FIXED)
    
    @property
    def prepay_complete(self):
        """ 如果预付款超过设定预付比例的50%，则认为预付已完成 """
        return round(self.prepay) >= round(self.total_fee*self.prepay_cent)*0.5
    
    
    
class PurchaseItem(models.Model):
    """ 采购项目 """
    
    purchase     = models.ForeignKey(Purchase,related_name='purchase_items',verbose_name='采购单')
    supplier_item_id = models.CharField(max_length=64,blank=True,verbose_name='供应商货号')
    
    product_id   = models.IntegerField(null=True,verbose_name='商品ID')
    sku_id       = models.IntegerField(null=True,verbose_name='规格ID')
    
    outer_id     = models.CharField(max_length=32,null=False,blank=True,verbose_name='商品编码')
    name         = models.CharField(max_length=64,null=False,blank=True,verbose_name='商品名称')
    outer_sku_id     = models.CharField(max_length=32,null=False,blank=True,verbose_name='规格编码')
    properties_name  = models.CharField(max_length=64,null=False,blank=True,verbose_name='规格属性')
    
    purchase_num = models.IntegerField(null=True,default=0,verbose_name='采购数量')
    storage_num  = models.IntegerField(null=True,default=0,verbose_name='已入库数')
    
    discount     = models.FloatField(null=True,default=0,verbose_name='折扣')
    std_price    = models.FloatField(default=0.0,verbose_name='实际进价')
    price        = models.FloatField(default=0.0,verbose_name='标准进价')
    
    total_fee    = models.FloatField(default=0.0,verbose_name='总费用')
    prepay       = models.FloatField(default=0.0,verbose_name='预付款')
    payment      = models.FloatField(default=0.0,verbose_name='已付款')

    created      = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='创建日期')
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='修改日期')
    
    status       = models.CharField(max_length=12,db_index=True,choices=PRODUCT_STATUS,
                                    default=pcfg.NORMAL,verbose_name='状态')
    
    arrival_status    = models.CharField(max_length=12,db_index=True,choices=PURCHASE_ARRIVAL_STATUS,
                                    default=pcfg.PD_UNARRIVAL,verbose_name='到货状态')
    
    extra_info   = models.CharField(max_length=1000,blank=True,verbose_name='备注')
    
    class Meta:
        db_table = 'supply_purchase_item'
        unique_together = ("purchase","product_id", "sku_id")
        verbose_name = u'采购项目'
        verbose_name_plural = u'采购项目列表'
        permissions = [
                       ("can_storage_confirm", u"确认入库数量"),
                       ]
    
    def __unicode__(self):
        return '<%s,%s,%s>'%(str(self.id or ''),self.outer_id,self.outer_sku_id)


class PurchasePayment(models.Model):
    """ 
        采购付款单 付款类型：
        1,货到付款
        2,预付款
        3,付款提货
    """    
    origin_nos   = models.TextField(blank=True,verbose_name='原单据号')
    
    pay_type     = models.CharField(max_length=6,db_index=True,choices=PURCHASE_PAYMENT_TYPE,verbose_name='付款类型')
    
    payment      = models.FloatField(default=0,verbose_name='付款金额')
    
    supplier     = models.ForeignKey(Supplier,null=True,blank=True,related_name='purchase_payments',verbose_name='收款方')
    
    status       = models.CharField(max_length=12,db_index=True,choices=PAYMENT_STATUS,
                                    default=pcfg.PP_WAIT_APPLY,verbose_name='状态')
    
    applier      = models.CharField(max_length=32,db_index=True,blank=True,verbose_name='申请人')
    cashier      = models.CharField(max_length=32,db_index=True,blank=True,verbose_name='付款人')
    
    pay_no       = models.CharField(max_length=256,db_index=True,blank=True,verbose_name='付款流水单号')
    pay_bank     = models.CharField(max_length=128,blank=True,verbose_name='付款银行(平台)')
    
    apply_time   = models.DateTimeField(null=True,blank=True,verbose_name='申请日期')
    pay_time     = models.DateTimeField(null=True,blank=True,verbose_name='付款日期')
    
    created      = models.DateTimeField(null=True,blank=True,auto_now=True,verbose_name='创建日期')
    modified     = models.DateTimeField(null=True,blank=True,auto_now_add=True,verbose_name='修改日期')
    
    extra_info   = models.TextField(max_length=1000,blank=True,verbose_name='备注')
    
    class Meta:
        db_table = 'shop_purchases_payment'
        verbose_name=u'采购付款单'
        verbose_name_plural = u'采购付款单列表'
        permissions = [
                       ("can_payment_confirm", u"确认采购付款"),
                       ]
        
    
    def __unicode__(self):
        return '<%s,%s,%.2f>'%(str(self.id or '') ,self.pay_type,self.payment)