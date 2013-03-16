#-*- coding:utf8 -*-
__author__ = 'meixqhi'
import os.path
import json
from django.db import models
from django.conf import settings
from django.db.models import Sum
from shopback import paramconfig as pcfg
from shopback.items.models import Item,Product,ProductSku
from shopback.orders.models import Trade
from shopback.fenxiao.models import PurchaseOrder
from shopback.trades.models import MergeTrade,MergeOrder
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
        verbose_name = u'待审核规则'
        
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
    outer_id = models.CharField(max_length=64,db_index=True,blank=True,verbose_name=u'商品外部编码')
    outer_sku_id = models.CharField(max_length=64,db_index=True,blank=True,verbose_name=u'商品规格编码')
    
    payment  = models.IntegerField(null=True,blank=True,verbose_name=u'大于金额')
    type     = models.CharField(max_length=10,choices=RULE_TYPE_CHOICE,verbose_name=u'规则类型')
    
    extra_info = models.TextField(blank=True,verbose_name=u'信息')
    
    created  = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    modified = models.DateTimeField(null=True,blank=True,auto_now=True)
    
    class Meta:
        db_table = 'shop_memorule_composerule'
        verbose_name=u'匹配规则'
        unique_together = ("outer_id","outer_sku_id")
        
    def __unicode__(self):
        return str(self.id)
    
    
    
class ComposeItem(models.Model):
    #匹配后的拆分商品
    
    compose_rule = models.ForeignKey(ComposeRule,related_name="compose_items",verbose_name=u'商品规则')
    
    outer_id     = models.CharField(max_length=64,db_index=True,blank=True,verbose_name=u'组合商品外部编码')
    outer_sku_id = models.CharField(max_length=64,db_index=True,blank=True,verbose_name=u'组合商品规格编码')
    num = models.IntegerField(default=1,verbose_name=u'商品数量')
    
    extra_info = models.TextField(blank=True,verbose_name=u'信息')
    
    created  = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    modified = models.DateTimeField(null=True,blank=True,auto_now=True)
    class Meta:
        db_table = 'shop_memorule_composeitem'
        verbose_name=u'规则组合商品'
        
    def __unicode__(self):
        return str(self.id)
    
    
    
def rule_match_product(sender, trade_id, *args, **kwargs):
    #匹配规则
    is_rule_match = False
    try:
        trade = MergeTrade.objects.get(id=trade_id)
    except Trade.DoesNotExist:
        pass
    else: 
        orders  = trade.merge_trade_orders.filter(sys_status=pcfg.IN_EFFECT)
        for order in orders:
            outer_id     = order.outer_id
            outer_sku_id = order.outer_sku_id
            prod_sku = None
            prod     = None
            if outer_sku_id:
                try:
                    prod_sku = ProductSku.objects.get(product__outer_id=outer_id,outer_id=outer_sku_id)
                except:
                    continue
                else:
                    if not prod_sku.is_match:
                        continue 
            else:
                try:
                    prod     = Product.objects.get(outer_id=outer_id)
                except:
                    continue
                else:
                    if not prod.is_match:
                        continue 
            is_rule_match = True
            order.is_rule_match = True
            order.save()
            
        if is_rule_match:
            raise Exception('订单商品有匹配')


rule_signal.connect(rule_match_product,sender='product_rule',dispatch_uid='rule_match_product')
 

def rule_match_trade(sender, trade_id, *args, **kwargs):
    
    try:
        trade = Trade.objects.get(id=trade_id)
    except Trade.DoesNotExist:
        pass
    else:
        orders = trade.trade_orders.exclude(refund_status__in=pcfg.REFUND_APPROVAL_STATUS)
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
    
        MergeTrade.objects.filter(id=trade_id).update(sys_memo=','.join(memo_list))
        
#rule_signal.connect(rule_match_trade,sender='trade_rule',dispatch_uid='rule_match_orders')


def rule_match_payment(sender, trade_id, *args, **kwargs):
    """
    赠品规则:
        1,针对实付订单，不能根据有效来计算，由于需拆分的实付订单拆分后会变成无效；
        2，赠品是根据最大匹配金额来赠送；
        3，该规则执行前，应先将所以满就送的订单删除；
    """
    try:
        trade = MergeTrade.objects.get(id=trade_id)
    except MergeTrade.DoesNotExist:
        pass
    else:
        trade.merge_trade_orders.filter(gift_type=pcfg.OVER_PAYMENT_GIT_TYPE).delete()
        try:
            orders = trade.merge_trade_orders.filter(gift_type=pcfg.REAL_ORDER_GIT_TYPE
                            ,status__in=(pcfg.WAIT_SELLER_SEND_GOODS,pcfg.WAIT_BUYER_CONFIRM_GOODS)
                            ).exclude(refund_status=pcfg.REFUND_SUCCESS)
            
            payment = orders.aggregate(total_payment=Sum('payment'))['total_payment'] or 0
            post_fee = trade.post_fee or 0
            
            real_payment = payment - float(post_fee)
            self_rule = None
            payment_rules = ComposeRule.objects.filter(type='payment').order_by('-payment')
            for rule in payment_rules:
                if real_payment >= rule.payment:
                    for item in rule.compose_items.all():
                        MergeOrder.gen_new_order(trade.id,item.outer_id,item.outer_sku_id,item.num,gift_type=pcfg.OVER_PAYMENT_GIT_TYPE)
                    break
            
            MergeTrade.objects.filter(id=trade_id).update(total_num=orders.filter(sys_status=pcfg.IN_EFFECT).count(),payment=payment)
        except Exception,exc:
            logger.error(exc.message or 'payment rule error',exc_info=True)
            trade.append_reason_code(pcfg.PAYMENT_RULE_ERROR_CODE)
            
rule_signal.connect(rule_match_payment,sender='payment_rule',dispatch_uid='rule_match_payment')


def rule_match_combose_split(sender, trade_id, *args, **kwargs):
    """
    拆分规则:
        1,针对实付订单，不能根据有效来计算，由于需拆分的实付订单拆分后会变成无效；
        2，赠品是根据最大匹配金额来赠送；
        3，该规则执行前，应先将所以满就送的订单删除；
    """
    try:
        trade = MergeTrade.objects.get(id=trade_id)
    except MergeTrade.DoesNotExist:
        pass
    else:
        trade.merge_trade_orders.filter(gift_type=pcfg.COMBOSE_SPLIT_GIT_TYPE).delete()
        try:
            orders = trade.merge_trade_orders.filter(gift_type=pcfg.REAL_ORDER_GIT_TYPE
                            ,status__in=(pcfg.WAIT_SELLER_SEND_GOODS,pcfg.WAIT_BUYER_CONFIRM_GOODS)
                            ).exclude(refund_status=pcfg.REFUND_SUCCESS)
            for order in orders:
                outer_id     = order.outer_id
                outer_sku_id = order.outer_sku_id
                order_num    = order.num
                prod_sku = None
                prod     = None
                if outer_sku_id:
                    try:
                        prod_sku = ProductSku.objects.get(product__outer_id=outer_id,outer_id=outer_sku_id)
                    except:
                        trade.append_reason_code(pcfg.OUTER_ID_NOT_MAP_CODE)
                        continue
                    else:
                        if not prod_sku.is_split:
                            continue
                else:
                    try:
                        prod     = Product.objects.get(outer_id=outer_id)
                    except:
                        trade.append_reason_code(pcfg.OUTER_ID_NOT_MAP_CODE)
                    else:
                        if not prod.is_split:
                            continue            
                try:
                    compose_rule = ComposeRule.objects.get(outer_id=outer_id,outer_sku_id=outer_sku_id,type='product')
                except Exception,exc:
                    pass
                else:
                    for item in compose_rule.compose_items.all():
                        MergeOrder.gen_new_order(trade.id,outer_id,outer_sku_id,
                                                 item.num*order_num,gift_type=pcfg.COMBOSE_SPLIT_GIT_TYPE)
                    order.sys_status=pcfg.INVALID_STATUS
                    order.save()
                    
        except Exception,exc:
            logger.error(exc.message or 'combose split error',exc_info=True)
            trade.append_reason_code(pcfg.COMPOSE_RULE_ERROR_CODE)

rule_signal.connect(rule_match_combose_split,sender='combose_split_rule',dispatch_uid='rule_match_combose_split')    

