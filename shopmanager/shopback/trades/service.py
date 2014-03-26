# -*- coding: utf-8 -*-
from .models import MergeTrade,MergeOrder

class TradeService(object):
    
    trade = None        
        
    def setTrade(self,trade):
        self.trade = trade

    def createTrade(self,id,trade_type):
        pass 
    
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