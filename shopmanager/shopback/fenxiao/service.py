# -*- coding: utf-8 -*-
from shopback.users import Seller
from shopback.trades.mixins import TaobaoTradeSercie,TaobaoSendTradeMixin
from shopback.fenxiao.models import FenxiaoProduct,PurchaseOrder,SubPurchaseOrder

class PurchaseOrderService(TaobaoTradeSercie,TaobaoSendTradeMixin):
    
    trade = None        
        
    def __init__(self,t):
        assert t not in ('',None)
        
        if isinstance(t,PurchaseOrder):
            self.trade = t
        else:
            self.trade = PurchaseOrder.objects.get(id=t)
    
    @classmethod
    def getPurchaseOrderInfo(cls,user_id,fenxiao_id):
        
        response    = apis.taobao_fenxiao_orders_get(purchase_order_id=fenxiao_id,
                                                     tb_user_id=user_id)
        return response['fenxiao_orders_get_response']['purchase_orders']['purchase_order'][0]
    
    @classmethod
    def saveSubPurchaseOrderByDict(cls,order_dict):
        
        sub_purchase_order,state= SubPurchaseOrder.objects.\
                    get_or_create(fenxiao_id=order_dict['fenxiao_id'])

        for k,v in sub_order.iteritems():
            hasattr(sub_purchase_order,k) and setattr(sub_purchase_order,k,v)
            
        sub_purchase_order.purchase_order  = purchase_order
        sub_purchase_order.fenxiao_product = FenxiaoProduct.get_or_create(
                                            seller_id,order_dict['item_id'])

        sub_purchase_order.save()
        
        return sub_purchase_order
    
    @classmethod
    def savePurchaseOrderByDict(cls,user_id,trade_dict):
        
        purchase_order,state = PurchaseOrder.objects.\
                    get_or_create(fenxiao_id=trade_dict['fenxiao_id'])
        purchase_order.user  = Seller.objects.get(visitor_id=user_id)
        purchase_order.seller_id  =  user_id
        sub_purchase_orders  = purchase_order_dict.pop('sub_purchase_orders')   
        
        for k,v in purchase_order_dict.iteritems():
            hasattr(purchase_order,k) and setattr(purchase_order,k,v)
    
        purchase_order.save()
        
        for sub_order in  sub_purchase_orders['sub_purchase_order']:
            cls.saveSubPurchaseOrderByDict(sub_order)
            
        return purchase_order
        
    
    @classmethod
    def createTrade(cls,user_id,tid):
        
        trade_dict = cls.getTradeInfo(user_id, tid)
        
        return cls.saveTradeByDict(user_id, trade_dict)

    
    def payTrade(self):
        pass
    
    def finishTrade(self):
        pass
    
    def closeTrade(self):
        pass
    
    def modifyTrade(self):
        pass