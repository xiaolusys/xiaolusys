# -*- coding: utf-8 -*-

from shopback.trades.mixins import TaobaoTradeService,TaobaoSendTradeMixin
from shopback.users import Seller
from shopback.orders.models import Trade,Order
from shopback.trades.models import MergeTrade,MergeOrder,map_trade_from_to_code
from shopback import paramconfig as pcfg
from common.utils import parse_datetime
from auth import apis

class OrderService(TaobaoTradeService,TaobaoSendTradeMixin):
    
    trade = None
        
    def __init__(self,t):
        assert t not in ('',None)
        
        if isinstance(t,Trade):
            self.trade = t
        else:
            self.trade = Trade.objects.get(id=t)
    
    @classmethod
    def getTradeFullInfo(cls,user_id,tid,*args,**kwargs):
        
        update_fields = 'seller_nick,buyer_nick,title,type,created,tid,status,modified,payment,discount_fee,'\
                    +'adjust_fee,post_fee,total_fee,point_fee,pay_time,end_time,consign_time,price,shipping_type,'\
                    +'receiver_name,receiver_state,receiver_city,receiver_district,receiver_address,receiver_zip'\
                    +',receiver_mobile,receiver_phone,buyer_message,buyer_memo,seller_memo,seller_flag,'\
                    +'send_time,is_brand_sale,is_force_wlb,trade_from,is_lgtype,lg_aging,orders,'
                    
        response    = apis.taobao_trade_fullinfo_get(tid=tid,fields=update_fields,tb_user_id=user_id)
        return response['trade_fullinfo_get_response']['trade']
    
    @classmethod
    def getTradeInfo(cls,user_id,tid,*args,**kwargs):
        
        update_fields = 'seller_nick,buyer_nick,title, type,created,tid,seller_rate,buyer_rate,status'\
                    +',payment,discount_fee,adjust_fee,post_fee,total_fee,pay_time,end_time,modified'\
                    +',consign_time,buyer_memo,seller_memo,alipay_no,buyer_message,'\
                    +'cod_fee,cod_status,shipping_type,orders',
                    
        response    = apis.taobao_trade_get (tid=tid,fields=update_fields,tb_user_id=user_id)
        return response['trade_get_response']['trade']
    
    @classmethod
    def saveOrderByDict(cls,order_dict,*args,**kwargs):
        
        order,state = Order.objects.get_or_create(pk=o['oid'])
        order.trade = trade
        
        for k,v in o.iteritems():
            hasattr(order,k) and setattr(order,k,v)
        
        order.outer_id  = o.get('outer_iid','')
        order.save()
        
        return order
    
    @classmethod
    def saveTradeByDict(cls,user_id,trade_dict,*args,**kwargs):
        
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
    def createTrade(cls,user_id,tid,*args,**kwargs):
        
        trade_dict = cls.getTradeInfo(user_id, tid)
        
        return cls.saveTradeByDict(user_id, trade_dict)
    
    @classmethod
    def createMergeOrder(cls,merge_trade,order,*args,**kwargs):
        
        merge_order,state = MergeOrder.objects.get_or_create(oid=order.oid,
                                                             tid=merge_trade.tid,
                                                             merge_trade = merge_trade)
        state = state or not merge_order.sys_status
        
        if state and order.refund_status in (pcfg.REFUND_WAIT_SELLER_AGREE,pcfg.REFUND_SUCCESS)\
                or order.status in (pcfg.TRADE_CLOSED,pcfg.TRADE_CLOSED_BY_TAOBAO):
            sys_status = pcfg.INVALID_STATUS
        else:
            sys_status = merge_order.sys_status or pcfg.IN_EFFECT
        
        if state:
            order_fields = ['num_iid','title','price','sku_id','num','outer_id'
                            ,'outer_sku_id','total_fee','payment','refund_status'
                            ,'pic_path','seller_nick','buyer_nick','created'
                            ,'pay_time','consign_time','status']
            
            for k in order_fields:
                setattr(merge_order,k,getattr(order,k))
            
            merge_order.sku_properties_name = order.properties_values
            merge_order.sys_status = sys_status
        else:
            merge_order.refund_status = order.refund_status
            merge_order.payment = order.payment
            merge_order.pay_time = order.pay_time
            merge_order.consign_time = order.consign_time
            merge_order.status   = order.status
            merge_order.sys_status = sys_status
        merge_order.save()
        
        return merge_order
    
    @classmethod
    def createMergeTrade(cls,trade,*args,**kwargs):
        
        tid  = trade.id
        merge_trade,state = MergeTrade.objects.get_or_create(tid=tid)
        
        update_fields = ['user','seller_id','seller_nick','buyer_nick','type'
                         ,'seller_cod_fee','buyer_cod_fee','cod_fee','cod_status'
                         ,'seller_flag','created','pay_time','modified','consign_time'
                         ,'send_time','status','is_brand_sale','is_lgtype','lg_aging'
                         ,'lg_aging_type','buyer_rate','seller_rate','seller_can_rate'
                         ,'is_part_consign','step_paid_fee','step_trade_status']
        
        if not merge_trade.receiver_name and trade.receiver_name:
            
            address_fields = ['receiver_name','receiver_state',
                             'receiver_city','receiver_district',
                             'receiver_address','receiver_zip',
                             'receiver_mobile','receiver_phone']
            
            update_fields.extend(address_fields)
        
        for k in update_fields:
            setattr(merge_trade,k,getattr(trade,k))
            
        merge_trade.payment   = merge_trade.payment or trade.payment
        merge_trade.total_fee   = merge_trade.total_fee or trade.total_fee
        merge_trade.discount_fee   = merge_trade.discount_fee or trade.discount_fee
        merge_trade.adjust_fee   = merge_trade.adjust_fee or trade.adjust_fee
        merge_trade.post_fee   = merge_trade.post_fee or trade.post_fee
        
        merge_trade.trade_from    = map_trade_from_to_code(trade.trade_from)
        merge_trade.alipay_no     = trade.buyer_alipay_no
        merge_trade.shipping_type = merge_trade.shipping_type or \
                pcfg.SHIPPING_TYPE_MAP.get(trade.shipping_type,pcfg.EXPRESS_SHIPPING_TYPE)
        
        update_model_fields(merge_trade,update_fields=update_fields
                            +['shipping_type','payment','total_fee',
                              'discount_fee','adjust_fee','post_fee',
                              'alipay_no','trade_from'])
        
        for order in trade.trade_orders.all():
            cls.createMergeOrder(merge_trade,order)
            
        return merge_trade
    
    
    def payTrade(self,*args,**kwargs):
        
        trade_dict = self.getTradeFullInfo(self.get_seller_id(),self.get_trade_id())
        trade = self.saveTradeByDict(self.get_seller_id(), trade_dict)
        
        return self.createMergeTrade(trade)
    
    def finishTrade(self,finish_time,*args,**kwargs):
        
        self.trade.end_time = finish_time
        self.trade.status   = pcfg.TRADE_FINISHED
        self.save()
        
        self.trade.trade_orders.filter(status=pcfg.WAIT_BUYER_CONFIRM_GOODS)\
                                .update(status=pcfg.TRADE_FINISHED)
            
    def closeTrade(self,*args,**kwargs):
        pass
    
    def changeTrade(self,*args,**kwargs):
        pass
    
    def changeTradeOrder(self,oid,*args,**kwargs):
        pass
    
    def remindTrade(self,*args,**kwargs):
        pass
    
    
    