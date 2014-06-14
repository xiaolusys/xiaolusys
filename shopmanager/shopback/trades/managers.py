#-*- coding:utf8 -*-
from django.db import models
from django.db.models import Q,Sum
from django.db.models.signals import post_save
from django.db import IntegrityError, transaction

from shopback import paramconfig as pcfg
from shopback.orders.models import Trade,Order
from shopback.fenxiao.models import PurchaseOrder
from shopback.items.models import Product,ProductSku
from shopback.signals import rule_signal,recalc_fee_signal
from common.utils import update_model_fields


class MergeTradeManager(models.Manager):
    
    def isFenxiaoType(cls,trade_type,*args,**kwargs):
        return trade_type == pcfg.FENXIAO_TYPE
    
    def isTaobaoType(cls,trade_type,*args,**kwargs):
        return trade_type == pcfg.TAOBAO_TYPE
    
    def isJingDongType(cls,trade_type,*args,**kwargs):
        return trade_type == pcfg.JD_TYPE
    
    def isYiHaoDianType(cls,trade_type,*args,**kwargs):
        return trade_type == pcfg.YHD_TYPE
    
    def isWeixinType(cls,trade_type,*args,**kwargs):
        return trade_type == pcfg.WX_TYPE
    
    def isAMZType(cls,trade_type,*args,**kwargs):
        return trade_type == pcfg.AMZ_TYPE
    
    def isDangDangType(cls,trade_type,*args,**kwargs):
        return trade_type == pcfg.DD_TYPE
    
    def isDirectType(cls,trade_type,*args,**kwargs):
        return trade_type == pcfg.DIRECT_TYPE
    
    def isExchangeType(cls,trade_type,*args,**kwargs):
        return trade_type == pcfg.EXCHANGE_TYPE
    
    def isReissueType(cls,trade_type,*args,**kwargs):
        return trade_type == pcfg.REISSUE_TYPE
    
    def get_queryset(self):
        
        super_tm = super(MergeTradeManager,self)
        #adapt to higer version django(>1.4)
        if hasattr(super_tm,'get_query_set'):
            return super_tm.get_query_set()
        return super_tm.get_queryset()
        
    
    def getMergeQueryset(self,buyer_nick, 
                          receiver_name, 
                          receiver_mobile,
                          receiver_phone):
        
        q = Q(receiver_name=receiver_name,buyer_nick=buyer_nick)
        if receiver_mobile :
            q = q|Q(receiver_mobile=receiver_mobile)
                
        if receiver_phone:
            q = q|Q(receiver_phone=receiver_phone)
            
        return self.get_queryset().filter(q)\
                .exclude(sys_status__in=(pcfg.EMPTY_STATUS,
                                         pcfg.FINISHED_STATUS,
                                         pcfg.INVALID_STATUS))
                
    def getMainMergeTrade(self,trade):
        
        merge_queryset = self.getMergeQueryset(
                                            trade.buyer_nick,
                                            trade.receiver_name,
                                            trade.receiver_mobile,
                                            trade.receiver_phone)\
                             .filter(has_merge=True)
        if merge_queryset.count() > 0:
            return merge_queryset[0]
        return None
        
        
    def mergeMaker(self,trade,sub_trade):
        
        from shopback.trades.options import mergeMaker
        return mergeMaker(trade,sub_trade)
    
    def mergeRemover(self,trade):
        
        from shopback.trades.options import mergeRemover
        return mergeRemover(trade)
        
    def driveMergeTrade(self,trade):
        
        from shopback.trades.options import driveMergeTrade
        return driveMergeTrade(trade)
    
    def updateWaitPostNum(self,trade):
        
        if outer_sku_id :
            ProductSku.objects.get(outer_id=outer_sku_id,
                                    product__outer_id=outer_id)
        else:
            Product.objects.get(outer_id=outer_id)
            product.update_wait_post_num(order.num)
    
    def isOrderDefect(self,outer_id,outer_sku_id):
        
        try:
            if outer_sku_id :
                ProductSku.objects.get(outer_id=outer_sku_id,
                                       product__outer_id=outer_id)
            else:
                Product.objects.get(outer_id=outer_id)
        except (Product.DoesNotExist,ProductSku.DoesNotExist):
            return True
        return False
            
    def isTradeDefect(self,trade):
        
        for order in trade.inuse_orders:
            if self.isOrderDefect(order.outer_id,
                                  order.outer_sku_id):
                return True
        return False
        
            
    def isTradeOutStock(self,trade):
        
        for order in trade.inuse_orders:
            if Product.objects.isProductOutOfStock(order.outer_id,
                                                   order.outer_sku_id):
                return True
        return False

    
    def isTradeFullRefund(self,trade):
        
        if not isinstance(trade,self.model):
            trade = self.get(id=trade)  

        refund_approval_num = trade.merge_orders.filter(
                            refund_status__in=pcfg.REFUND_APPROVAL_STATUS,
                            gift_type=pcfg.REAL_ORDER_GIT_TYPE,
                            is_merge=False)\
                            .count()
                            
        total_orders_num  = trade.merge_orders.filter(
                            gift_type=pcfg.REAL_ORDER_GIT_TYPE,
                            is_merge=False).count()

        if refund_approval_num == total_orders_num:
            return True
        return False

    
    def isTradeNewRefund(self,trade):
        
        if not isinstance(trade,self.model):
            trade = self.get(id=trade) 
            
        refund_orders_num   = trade.merge_orders.filter(
                                    gift_type=pcfg.REAL_ORDER_GIT_TYPE,
                                    is_merge=False)\
                              .exclude(refund_status=pcfg.NO_REFUND).count()
        
        if refund_orders_num >trade.refund_num:
            
            trade.refund_num = refund_orders_num
            update_model_fields(trade,update_fields=['refund_num'])
            return True
        
        return False
        
    def isTradeRefunding(self,trade):
        
        orders = trade.merge_orders.filter(
                        refund_status=pcfg.REFUND_WAIT_SELLER_AGREE)
        if orders.count()>0:
            return True
        return False
        
    def isOrderRuleMatch(self,order):
        
        return Product.objects.isProductRuelMatch(order.outer_id,
                                                  order.outer_sku_id)
        
    def isTradeRuleMatch(self,trade):
        
        for order in trade.inuse_orders:
            if self.isOrderRuleMatch(order):
                return True
        return False

        
    def isTradeMergeable(self,trade):
        
        if not isinstance(trade,self.model):
            trade = self.get(id=trade) 
            
        queryset = self.getMergeQueryset(trade.buyer_nick,
                                         trade.receiver_name,
                                         trade.receiver_mobile,
                                         trade.receiver_phone)
        trades = queryset.exclude(id=trade.id)
        
        return trades.count() > 0
            
    
    def isValidPubTime(cls,trade,modified):
        
        if not isinstance(trade,self.model):
            trade = self.get(tid=trade) 

        if (not trade.modified or 
            trade.modified < modified or 
            not trade.sys_status):
            
                return True
        return False


    def mapTradeFromToCode(self,trade_from):
        
        from_code = 0
        from_list = trade_from.split(',')
        for f in from_list:
            from_code |= TF_CODE_MAP.get(f.upper(),0)
            
        return from_code
    
    
 