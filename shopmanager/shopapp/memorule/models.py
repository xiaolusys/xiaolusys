#-*- coding:utf8 -*-
__author__ = 'meixqhi'
import os.path
import json
from django.db import models
from django.conf import settings
from shopback.items.models import Item,Product,ProductSku
from shopback.orders.models import Trade,REFUND_APPROVAL_STATUS
from shopback.fenxiao.models import PurchaseOrder
from shopback.trades.models import MergeTrade,MergeOrder,WAIT_SELLER_SEND_GOODS,CONFIRM_WAIT_SEND_GOODS,WAIT_CONFIRM_WAIT_SEND_GOODS,IN_EFFECT,INVALID_STATUS
from shopback.monitor.models import COMPOSE_RULE_ERROR_CODE
from shopback.signals import rule_signal
import logging

logger = logging.getLogger('memorule.handler')


RULE_STATUS = (
    ('US','使用'),
    ('SX','失效'),
)
SCOPE_CHOICE = (
    ('trade','交易域'),
    ('product','商品域'),
)
RULE_TYPE_CHOICE = (
    ('payment','金额规则'),
    ('product','商品规则'),
)

class TradeRule(models.Model):

    formula     = models.CharField(max_length=64,blank=True,)
    memo        = models.CharField(max_length=64,blank=True,)

    formula_desc = models.TextField(max_length=256,blank=True,)

    scope       = models.CharField(max_length=10,choices=SCOPE_CHOICE,)
    status      = models.CharField(max_length=2,choices=RULE_STATUS,)

    items       = models.ManyToManyField(Item,related_name='rules',symmetrical=False,db_table='shop_memorule_itemrulemap')
    class Meta:
        db_table = 'shop_memorule_traderule'


FIELD_TYPE_CHOICE = (
    ('single','单选'),
    ('check','复选'),
    ('text','文本'),
)
class RuleFieldType(models.Model):

    field_name = models.CharField(max_length=64,primary_key=True)
    field_type = models.CharField(max_length=10,choices=FIELD_TYPE_CHOICE)

    alias      = models.CharField(max_length=64)
    default_value = models.TextField(max_length=256,blank=True)

    class Meta:
        db_table = 'shop_memorule_rulefieldtype'

    def __unicode__(self):
        return self.field_name+self.field_type




class ProductRuleField(models.Model):

    outer_id    = models.CharField(max_length=64,db_index=True)
    field      = models.ForeignKey(RuleFieldType)

    custom_alias   = models.CharField(max_length=256,blank=True)
    custom_default = models.TextField(max_length=256,blank=True)

    class Meta:
        db_table = 'shop_memorule_productrulefield'

    @property
    def alias(self):
        return self.custom_alias or self.field.alias

    @property
    def default(self):
        value = self.custom_default or self.field.default_value
        if self.field.field_type == 'check' or self.field.field_type == 'single':
            return value.split(',')
        return value

    def to_json(self):
        return [self.field.field_name,self.alias,self.field.field_type,self.default]
 
 
class RuleMemo(models.Model):
    
    tid   =  models.BigIntegerField(primary_key=True)
    
    is_used   = models.BooleanField(default=False)
    rule_memo      = models.TextField(max_length=1000,blank=True)
    seller_flag    = models.IntegerField(null=True)
    
    created  = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    modified = models.DateTimeField(null=True,blank=True,auto_now=True)
    
    class Meta:
        db_table = 'shop_memorule_rulememo'

    def __unicode__(self):
        return str(self.tid)
    
    
class ComposeRule(models.Model):
    #匹配规则
    outer_id = models.CharField(max_length=64,db_index=True,blank=True)
    outer_sku_id = models.CharField(max_length=64,db_index=True,blank=True)
    
    payment  = models.IntegerField(null=True,blank=True)
    type     = models.CharField(max_length=10,choices=RULE_TYPE_CHOICE)
    
    extra_info = models.TextField(blank=True)
    
    created  = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    modified = models.DateTimeField(null=True,blank=True,auto_now=True)
    
    class Meta:
        db_table = 'shop_memorule_composerule'
        verbose_name=u'匹配规则'
        
    def __unicode__(self):
        return str(self.id)
    
    
    
class ComposeItem(models.Model):
    #匹配后的拆分商品
    
    compose_rule = models.ForeignKey(ComposeRule,related_name="compose_items")
    
    outer_id     = models.CharField(max_length=64,db_index=True,blank=True)
    outer_sku_id = models.CharField(max_length=64,db_index=True,blank=True)
    num = models.IntegerField(default=1)
    
    extra_info = models.TextField(blank=True)
    
    created  = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    modified = models.DateTimeField(null=True,blank=True,auto_now=True)
    class Meta:
        db_table = 'shop_memorule_composeitem'
        verbose_name=u'规则组合商品'
        
    def __unicode__(self):
        return str(self.id)
    
    
    
def rule_match_product(sender, trade_tid, *args, **kwargs):
    try:
        trade = Trade.objects.get(id=trade_tid)
    except Trade.DoesNotExist:
        return 
    orders  = trade.trade_orders.exclude(refund_status__in=REFUND_APPROVAL_STATUS)
    for order in orders:
        rules = ProductRuleField.objects.filter(outer_id=order.outer_tid)
        if rules.count()>0:
            raise Exception('该交易需要规则匹配'.decode('utf8'))
        

rule_signal.connect(rule_match_product,sender='product_rule',dispatch_uid='rule_match_product')
 

def rule_match_trade(sender, trade_tid, *args, **kwargs):
    
    try:
        trade = Trade.objects.get(id=trade_tid)
    except Trade.DoesNotExist:
        pass
    else:
        orders = trade.trade_orders.exclude(refund_status__in=REFUND_APPROVAL_STATUS)
        trade_rules = TradeRule.objects.filter(scope='trade',status='US') 
        memo_list = []
        payment = 0 
        trade_payment = 0
        for order in orders:
            payment = float(order.payment)  
            trade_payment += payment
            item = Item.get_or_create(trade.seller_id,order.num_iid)
            order_rules = item.rules.filter(scope='product',status='US')
            for rule in order_rules:
                try:
                    if eval(rule.formula):
                        memo_list.append(rule.memo)
                except Exception,exc:
                    logger.error('交易商品规则(%s)匹配出错'.decode('utf8')%rule.formula,exc_info=True)
        
        trade.payment = trade_payment  
        for rule in trade_rules:
            try:
                if eval(rule.formula):
                    memo_list.append(rule.memo)
            except Exception,exc:
                logger.error('交易订单规则(%s)匹配出错'.decode('utf8')%rule.formula,exc_info=True)
    
        MergeTrade.objects.filter(tid=trade_tid).update(sys_memo=','.join(memo_list))
        

rule_signal.connect(rule_match_trade,sender='trade_rule',dispatch_uid='rule_match_orders')


def rule_match_merge_trade(sender, trade_tid, *args, **kwargs):
 
    try:
        trade = MergeTrade.objects.get(tid=trade_tid)
    except MergeTrade.DoesNotExist:
        pass
    else:
        try:
            orders = trade.merge_trade_orders.filter(status__in=(WAIT_SELLER_SEND_GOODS,CONFIRM_WAIT_SEND_GOODS,WAIT_CONFIRM_WAIT_SEND_GOODS)
                                                     ,sys_status=IN_EFFECT).exclude(refund_status__in=REFUND_APPROVAL_STATUS)
            payment = 0 
            for order in orders:
                payment += float(order.payment)
                try:
                    compose_rule = ComposeRule.objects.get(outer_id=order.outer_id,outer_sku_id=order.outer_sku_id,type='product')
                except:
                    pass
                else:
                    MergeOrder.filter(id=order.id).update(sys_status=INVALID_STATUS)
                    for item in compose_rule.compose_items.all():
                        MergeOrder.gen_new_order(trade_tid,item.outer_id,item.outer_sku_id,item.num)
    
            post_fee = trade.post_fee
            if not post_fee:
                try:
                    post_fee = Trade.objects.get(id=trade_tid).post_fee
                except:
                    post_fee = PurchaseOrder.objects.get(id=trade_tid).post_fee
            
            real_payment = payment - float(post_fee)
            self_rule = None
            payment_rules = ComposeRule.objects.filter(type='payment').order_by('-payment')
            for rule in payment_rules:
                if real_payment >= rule.payment:
                    for item in rule.compose_items.all():
                        MergeOrder.gen_new_order(trade_tid,item.outer_id,item.outer_sku_id,item.num)
                    break
        except Exception,exc:
            logger.error(exc.message,exc_info)
            trade.append_reason_code(COMPOSE_RULE_ERROR_CODE)
            
rule_signal.connect(rule_match_merge_trade,sender='merge_trade_rule',dispatch_uid='rule_match_merge_trade')


    
