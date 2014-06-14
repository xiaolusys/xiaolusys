# -*- coding: utf-8 -*-
from .models import MergeTrade,MergeOrder
from shopback.base.service import LocalService
from shopback.orders.service import OrderService
from shopback.fenxiao.service import PurchaseOrderService
from shopback import paramconfig as pcfg

TRADE_TYPE_SERVICE_MAP = {
    pcfg.FENXIAO_TYPE:PurchaseOrderService,
    pcfg.TAOBAO_TYPE:OrderService,
    pcfg.JD_TYPE:LocalService,
    pcfg.YHD_TYPE:LocalService,
    pcfg.DD_TYPE:LocalService,
    pcfg.WX_TYPE:LocalService,
    pcfg.AMZ_TYPE:LocalService,
    pcfg.DIRECT_TYPE:LocalService,
    pcfg.EXCHANGE_TYPE:LocalService,
    pcfg.REISSUE_TYPE:LocalService,
}

    
class TradeService(LocalService):
    
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
        
        return TRADE_TYPE_SERVICE_MAP.get(
                  self.trade.type,LocalService)(self.trade.tid)

        
    @classmethod
    def isTradeExist(cls,tid):
        try:
            MergeTrade.objects.get(tid=tid)
        except MergeTrade.DoesNotExist:
            return False
        return True
        
    
    @classmethod
    def getBaseServiceClass(cls,trade_type,*args,**kwargs):
        
        return TRADE_TYPE_SERVICE_MAP.get(trade_type,LocalService)
        
    
    @classmethod
    def createTrade(cls,user_id,tid,trade_type,*args,**kwargs):
        
        service_class = cls.getBaseServiceClass(trade_type)
        base_trade    = service_class.createTrade(user_id,tid)
        
        return  service_class.createMergeTrade(base_trade)
 
                
    def payTrade(self,*args,**kwargs):
        
        self.merge_trade = self.bservice.payTrade()
        
    
    def sendTrade(self,*args,**kwargs):

        if self.trade.type in (pcfg.EXCHANGE_TYPE,pcfg.DIRECT_TYPE,pcfg.REISSUE_TYPE):
            return 
        
        return self.bservice.sendTrade(company_code=self.trade.logistics_company.code,
                                       out_sid=self.trade.out_sid)
        
    def ShipTrade(self,*args,**kwargs):
        
        return self.bservice.shipTrade(*args,**kwargs)
    
    def finishTrade(self,*args,**kwargs):
        pass
    
    def closeTrade(self,*args,**kwargs):
        pass
    
    def memoTrade(self,*args,**kwargs):
        pass
        
    def changeTrade(self,*args,**kwargs):
        pass
    
    def changeTradeOrder(self,oid,*args,**kwargs):
        pass
    
    def remindTrade(self,*args,**kwargs):
        pass
    

