# -*- coding: utf-8 -*-
from .models import MergeTrade,MergeOrder
from shopback.orders.service import OrderService
from shopback.fenxiao.service import PurchaseOrderService
from shopback import paramconfig as pcfg

class TradeService(object):
    
    trade = None        
        
    def __init__(self,t):
        assert t not in ('',None)
        
        if isinstance(t,MergeTrade):
            self.trade = t
        else:
            self.trade = MergeTrade.objects.get(tid=t)
    
    @classmethod
    def getRealServiceClass(self,trade_type):
        
        if trade_type in (pcfg.FENXIAO_TYPE,pcfg.AGENT_TYPE,pcfg.DEALER_TYPE):
            return PurchaseOrderService
        
        if trade_type in (pcfg.TAOBAO_TYPE,pcfg.DIRECT_TYPE,
                          pcfg.AUTO_DELIVERY_TYPE,pcfg.COD_TYPE,
                          pcfg.GUARANTEE_TYPE,pcfg.AUCTION_TYPE):
            return OrderService
        
        return LocalService
    
    def createTrade(self,tid,trade_type):
        
        service_class = self.getRealServiceClass(trade_type)
        
    
    def payTrade(self):
        pass
    
    def sendTrade(self):
        
        if self.trade.type in (pcfg.EXCHANGE_TYPE,pcfg.DIRECT_TYPE,pcfg.REISSUE_TYPE):
            return False
    
    def finishTrade(self):
        pass
    
    def closeTrade(self):
        pass
    
    def modifyTrade(self):
        pass