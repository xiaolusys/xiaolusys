# -*- coding: utf-8 -*-
from .models import MergeTrade,MergeOrder
from shopback.orders.service import OrderService
from shopback.fenxiao.service import PurchaseOrderService
from shopback import paramconfig as pcfg

class TradeService(object):
    
    trade = None    
    bservice = None    
        
    def __init__(self,t):
        assert t not in ('',None)
        
        if isinstance(t,MergeTrade):
            self.trade = t
        else:
            self.trade = MergeTrade.objects.get(tid=t)
            
        self.bservice = self.getBaseService()
    
    def getBaseService(self):
        if self.__class__.isFenxiaoType(self.trade.type):
            return PurchaseOrderService(self.trade.tid)
        
        if self.__class__.isTaobaoType(self.trade.type):
            return OrderService(self.trade.tid)
    
    @classmethod
    def isTradeExist(cls,tid):
        try:
            MergeTrade.objects.get(tid=tid)
        except MergeTrade.DoesNotExist:
            return False
        return True
        
    @classmethod
    def isValidPubTime(cls,tid,pub_time):
        
        try:
            obj = MergeTrade.objects.get(tid=tid)
        except  MergeTrade.DoesNotExist:
            return True
        
        if not obj.modified or obj.modified < pub_time:
            return True
        
        return False    
    
    @classmethod
    def isFenxiaoType(cls,trade_type,*args,**kwargs):
        return trade_type in (pcfg.FENXIAO_TYPE,pcfg.AGENT_TYPE,pcfg.DEALER_TYPE)
    
    @classmethod
    def isTaobaoType(cls,trade_type,*args,**kwargs):
        return trade_type in (pcfg.TAOBAO_TYPE,pcfg.DIRECT_TYPE,
                          pcfg.AUTO_DELIVERY_TYPE,pcfg.COD_TYPE,
                          pcfg.GUARANTEE_TYPE,pcfg.AUCTION_TYPE)
    
    @classmethod
    def getBaseServiceClass(cls,trade_type,*args,**kwargs):
        
        if cls.isFenxiaoType(trade_type):
            return PurchaseOrderService
        
        if cls.isTaobaoType(trade_type):
            return OrderService
        
        return LocalService
    
    
    
    @classmethod
    def createTrade(cls,user_id,tid,trade_type,*args,**kwargs):
        
        service_class = cls.getBaseServiceClass(trade_type)
        base_trade    = service_class.createTrade(user_id,tid)
        
        return service_class.createMergeTrade(base_trade)
            
                
    def payTrade(self,*args,**kwargs):
        
        self.merge_trade = self.bservice.payTrade()
        
        
    
    def sendTrade(self,*args,**kwargs):
        
        if self.trade.type in (pcfg.EXCHANGE_TYPE,pcfg.DIRECT_TYPE,pcfg.REISSUE_TYPE):
            return False
    
    def finishTrade(self,*args,**kwargs):
        pass
    
    def closeTrade(self,*args,**kwargs):
        pass
    
    def changeTrade(self,*args,**kwargs):
        pass
    
    def changeTradeOrder(self,oid,*args,**kwargs):
        pass
    
    def remindTrade(self,*args,**kwargs):
        pass
    
    