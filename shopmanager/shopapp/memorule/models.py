#-*- coding:utf8 -*-
__author__ = 'meixqhi'
from django.db import models
from shopback.items.models import Item
from shopback.orders.models import Trade
from shopback.trades.models import MergeTrade,WAIT_PREPARE_SEND_STATUS,WAIT_SCAN_WEIGHT_STATUS,AUDITFAIL_STATUS,\
    WAIT_CONFIRM_SEND_STATUS,FINISHED_STATUS,INVALID_STATUS,ON_THE_FLY_STATUS,SYSTEM_SEND_TAOBAO_STATUS
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
SYS_STATUS_MATCH_FLAGS = {
    WAIT_PREPARE_SEND_STATUS:1, #已审核
    WAIT_SCAN_WEIGHT_STATUS:2,  #已开单
    WAIT_CONFIRM_SEND_STATUS:3, #已称重
    SYSTEM_SEND_TAOBAO_STATUS:3, #等待更新发货状态
    INVALID_STATUS:4,           #已作废
    AUDITFAIL_STATUS:4,         #问题单
    ON_THE_FLY_STATUS:5,        #表示已合并
}

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
    

def rule_match_product(sender, trade_id, *args, **kwargs):
    try:
        trade = Trade.objects.get(id=trade_id)
    except Trade.DoesNotExist:
        return 
    orders  = trade.trade_orders.filter(refund_status='NO_REFUND')
    for order in orders:
        rules = ProductRuleField.objects.filter(outer_id=order.outer_id)
        if rules.count()>0:
            raise Exception('该交易需要规则匹配')
        

rule_signal.connect(rule_match_product,sender='product_rule',dispatch_uid='rule_match_product')
 

def rule_match_trade(sender, trade_id, *args, **kwargs):
    try:
        trade = Trade.objects.get(id=trade_id)
    except Trade.DoesNotExist:
        pass
    else:
        orders = trade.trade_orders.filter(refund_status='NO_REFUND')
        trade_rules = TradeRule.objects.filter(scope='trade',status='US') 
        memo_list = []
        payment = 0 
        for order in orders:
            payment = float(order.payment)  
            item = Item.get_or_create(trade.seller_id,order.num_iid)
            order_rules = item.rules.filter(scope='product',status='US')
            for rule in order_rules:
                try:
                    if eval(rule.formula):
                        memo_list.append(rule.memo)
                except Exception,exc:
                    logger.error('交易商品规则(%s)匹配出错'%rule.formula,exc_info=True)
        
        trade.payment = payment  
        for rule in trade_rules:
            try:
                if eval(rule.formula):
                    memo_list.append(rule.memo)
            except Exception,exc:
                logger.error('交易订单规则(%s)匹配出错'%rule.formula,exc_info=True)
 
            
        MergeTrade.objects.filter(tid=trade_id).update(sys_memo=','.join(memo_list))
        

rule_signal.connect(rule_match_trade,sender='trade_rule',dispatch_uid='rule_match_trade')
    