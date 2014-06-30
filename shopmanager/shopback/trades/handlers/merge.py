#-*- coding:utf8 -*-
from django.conf import settings
from .handler import BaseHandler
from shopback.trades.models import MergeTrade
from shopback import paramconfig as pcfg
from shopapp.memorule import ruleMatchPayment
from common.modelutils import  update_model_fields

class MergeHandler(BaseHandler):
    
    def handleable(self,merge_trade,*args,**kwargs):
        return ((kwargs.get('first_pay_load',None) or 
                 kwargs.get('update_address',None)) and 
                MergeTrade.objects.isTradeMergeable(merge_trade))
        
    def process(self,merge_trade,*args,**kwargs):
        
        if settings.DEBUG:
            print 'DEBUG MERGE:',merge_trade
            
        merge_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
        
        buyer_nick       = trade.buyer_nick              #买家昵称
        receiver_mobile  = trade.receiver_mobile         #收货手机
        receiver_phone   = trade.receiver_phone          #收货手机
        receiver_name    = trade.receiver_name           #收货人
        receiver_address = trade.receiver_address        #收货地址
        full_address     = trade.buyer_full_address      #详细地址
        
        merge_queryset = MergeTrade.objects.getMergeQueryset( 
                            trade.buyer_nick , 
                            trade.receiver_name, 
                            trade.receiver_mobile, 
                            trade.receiver_phone)
        
        for mtrade in merge_queryset:
            mtrade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
        
        main_trade = MergeTrade.objects.driveMergeTrade(merge_trade)
        if main_trade:
            ruleMatchPayment(main_trade)
            
        
        
        
        
        
        