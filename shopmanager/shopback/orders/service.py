# -*- coding: utf-8 -*-

from shopback.trades.mixins import TaobaoTradeSercie,TaobaoSendTradeMixin
from shopback.users import Seller
from shopback.orders.models import Trade,Order
from shopback import paramconfig as pcfg
from common.utils import parse_datetime
from auth import apis

class OrderService(TaobaoTradeSercie,TaobaoSendTradeMixin):
    
    trade = None
        
    def __init__(self,t):
        assert t not in ('',None)
        
        if isinstance(t,Trade):
            self.trade = t
        else:
            self.trade = Trade.objects.get(id=t)
    
    @classmethod
    def getTradeFullInfo(cls,user_id,tid):
        
        response    = apis.taobao_trade_fullinfo_get(tid=tid,tb_user_id=user_id)
        return response['trade_fullinfo_get_response']['trade']
    
    @classmethod
    def getTradeInfo(cls,user_id,tid):
        
        response    = apis.taobao_trade_get (tid=tid,tb_user_id=user_id)
        return response['trade_get_response']['trade']
    
    @classmethod
    def saveOrderByDict(cls,order_dict):
        
        order,state = Order.objects.get_or_create(pk=o['oid'])
        order.trade = trade
        
        for k,v in o.iteritems():
            hasattr(order,k) and setattr(order,k,v)
        
        order.outer_id  = o.get('outer_iid','')
        order.save()
        
        return order
    
    @classmethod
    def saveTradeByDict(cls,user_id,trade_dict):
        
        if not trade_dict.get('tid'):
            return 
        
        trade,state = Trade.objects.get_or_create(pk=trade_dict['tid'])
        trade.user  = Seller.objects.get(visitor_id=user_id)
        trade.seller_id   = user_id
        
        for k,v in trade_dict.iteritems():
            hasattr(trade,k) and setattr(trade,k,v)
        
        trade.save()

        for o in trade_dict['orders']['order']:
            cls.saveOrderByDict(o)
            
        return trade
    
    @classmethod
    def createTrade(cls,user_id,tid):
        
        trade_dict = cls.getTradeInfo(user_id, tid)
        
        return cls.saveTradeByDict(user_id, trade_dict)
    
    def payTrade(self):
        
        trade_dict = self.getTradeFullInfo(self.get_seller_id(),self.get_trade_id())
        return self.saveTradeByDict(self.get_seller_id(), trade_dict)
    
    def finishTrade(self,finish_time):
        
        self.trade.end_time = finish_time
        self.trade.status   = pcfg.TRADE_FINISHED
        self.save()
        
        self.trade.trade_orders.filter(status=pcfg.WAIT_BUYER_CONFIRM_GOODS)\
                                .update(status=pcfg.TRADE_FINISHED)
            
    def closeTrade(self):
        pass
    
    
    def modifyTrade(self):
        pass
    
    