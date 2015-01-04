#-*- coding:utf8 -*-
__author__ = 'meixqhi'
import json
from django.db import models
from django.conf import settings
from django.db.models import Sum,F
from shopback import paramconfig as pcfg
from shopback.items.models import Product
from shopback.trades.models import MergeTrade,MergeOrder
from shopapp.memorule.models import ComposeRule,ComposeItem
from shopback.base import log_action,User, ADDITION, CHANGE
from common.utils import update_model_fields
import logging

logger = logging.getLogger('django.request')

def ruleMatchPayment(trade):
    """
    满就送规则:
        1,针对实付订单，不能根据有效来计算，由于需拆分的实付订单拆分后会变成无效；
        2，赠品是根据最大匹配金额来赠送；
        3，该规则执行前，应先将所以满就送的订单删除；
    """
    try:
        trade.merge_orders.filter(gift_type=pcfg.OVER_PAYMENT_GIT_TYPE).delete()
        
        real_payment = trade.inuse_orders.aggregate(
                        total_payment=Sum('payment'))['total_payment'] or 0
    
        payment_rules = ComposeRule.objects.filter(type=pcfg.RULE_PAYMENT_TYPE)\
                        .order_by('-payment')
        
        for rule in payment_rules:
            
            if real_payment < rule.payment or rule.gif_count <= 0:
                continue
            
            for item in rule.compose_items.all():
                
                MergeOrder.gen_new_order(trade.id,
                                         item.outer_id,
                                         item.outer_sku_id,
                                         item.num,
                                         gift_type=pcfg.OVER_PAYMENT_GIT_TYPE)
                
                log_action(trade.user.user.id,trade,CHANGE,
                           u'满就送（实付:%s）'%str(real_payment))
                
            ComposeRule.objects.filter(id=rule.id).update(gif_count=F('gif_count')-1)
            break
        
    except Exception,exc:
        trade.append_reason_code(pcfg.PAYMENT_RULE_ERROR_CODE)
        logger.error(u'满就送规则错误:%s'%exc.message ,exc_info=True)
        
  
  
def ruleMatchSplit(trade): 
     
    try:
        trade.merge_orders.filter(gift_type=pcfg.COMBOSE_SPLIT_GIT_TYPE).delete()
        
        for order in trade.inuse_orders:

            try:
                if not Product.objects.isProductRuleSplit(order.outer_id,
                                                          order.outer_sku_id):
                    continue
            
                compose_rule = ComposeRule.objects.get(outer_id=order.outer_id,
                                                       outer_sku_id=order.outer_sku_id,
                                                       type=pcfg.RULE_SPLIT_TYPE)
            except:
                continue
            else:
                items  = compose_rule.compose_items.all()
                
                total_cost = 0   #计算总成本
                for item in items:
                    total_cost += Product.objects.getPrudocutCostByCode(item.outer_id,
                                                                        item.outer_sku_id)
                
                for item in items:
                    cost    = Product.objects.getPrudocutCostByCode(item.outer_id,
                                                                    item.outer_sku_id)
                    
                    payment = total_cost and '%.2f'%(float(cost/total_cost)*float(order.payment)) or 0
                    
                    MergeOrder.gen_new_order(trade.id,
                                             item.outer_id,
                                             item.outer_sku_id,
                                             item.num*order.num,
                                             gift_type=pcfg.COMBOSE_SPLIT_GIT_TYPE,
                                             payment=payment)
                    
                order.sys_status=pcfg.INVALID_STATUS
                order.save()
         
                log_action(trade.user.user.id,trade,CHANGE,
                           u'拆分订单(%d,%s,%s)'%(order.id,order.outer_id,order.outer_sku_id))
                
    except Exception,exc:
        trade.append_reason_code(pcfg.COMPOSE_RULE_ERROR_CODE)
        logger.error(u'组合拆分出错：%s'%exc.message ,exc_info=True)
        
        
def ruleMatchGifts(trade): 
     
    try:
        trade.merge_orders.filter(gift_type=pcfg.ITEM_GIFT_TYPE).delete()
  
        orders = trade.merge_orders.filter(gift_type=pcfg.REAL_ORDER_GIT_TYPE
                        ,status__in=(pcfg.WAIT_SELLER_SEND_GOODS,
                                     pcfg.WAIT_BUYER_CONFIRM_GOODS)
                        ).exclude(refund_status=pcfg.REFUND_SUCCESS)
        for order in orders:
            try:
                if not Product.objects.isProductRuleSplit(order.outer_id,
                                                                                                order.outer_sku_id):
                    continue
                
                compose_rule = ComposeRule.objects.get(outer_id=order.outer_id,
                                                       outer_sku_id=order.outer_sku_id,
                                                       type=ComposeRule.RULE_GIFTS_TYPE)
            except :
                continue
            else:
                rules  = compose_rule.compose_items.all()
                
                for rule in rules:
                    gifts_num = rule.num*order.num
                    if compose_rule.gif_count >= gifts_num:
                        MergeOrder.gen_new_order(trade.id,
                                                 rule.outer_id,
                                                 rule.outer_sku_id,
                                                 gifts_num,
                                                 gift_type=pcfg.ITEM_GIFT_TYPE,
                                                 payment=0)
                        
                        compose_rule.gif_count -= gifts_num
                        
                        ComposeRule.objects.filter(id=rule.id).update(gif_count=F('gif_count')-gifts_num)

                msg = u'买(oid:%s)就送(%s)'%(order.id,','.join([ '%s-%s'%(r.outer_id,r.outer_sku_id) for r in rules]))
                log_action(trade.user.user.id,trade,CHANGE,msg)
                
    except Exception,exc:
        logger.error(exc.message or 'rule gifts error',exc_info=True)
        trade.append_reason_code(pcfg.COMPOSE_RULE_ERROR_CODE)    

        
        
        
