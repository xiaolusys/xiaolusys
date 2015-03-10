#-*- coding:utf8 -*-
import datetime
from django.conf import settings
from .handler import BaseHandler
from shopback.trades.models import MergeTrade
from shopback import paramconfig as pcfg
from shopapp.memorule import ruleMatchPayment
from common.modelutils import  update_model_fields

class MergeHandler(BaseHandler):
    
    def handleable(self,merge_trade,*args,**kwargs):
        return (kwargs.get('trade_merge_flag',True) and
                (kwargs.get('first_pay_load',None) or 
                 kwargs.get('update_address',None)) and 
                MergeTrade.objects.isTradeMergeable(merge_trade))
        
    def process(self,merge_trade,*args,**kwargs):
        
        if settings.DEBUG:
            print 'DEBUG MERGE:',merge_trade
            
        if merge_trade.type == MergeTrade.WX_TYPE:
            latest_paytime = datetime.datetime(merge_trade.pay_time.year
                                               ,merge_trade.pay_time.month
                                               ,merge_trade.pay_time.day) 
            
            merge_queryset = MergeTrade.objects.getMergeQueryset(
                                            merge_trade.buyer_nick,
                                            merge_trade.receiver_name,
                                            merge_trade.receiver_mobile,
                                            merge_trade.receiver_phone,
                                            latest_paytime=latest_paytime)
            
            merge_queryset = merge_queryset.exclude(id=merge_trade.id)
            
            if merge_queryset.count() == 0:
                return 
            
            merge_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
            
            main_trade = MergeTrade.objects.driveMergeTrade(merge_trade,
                                                            latest_paytime=latest_paytime)
            if main_trade:
                ruleMatchPayment(main_trade)
        else:

            merge_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
            
            main_trade = MergeTrade.objects.driveMergeTrade(merge_trade)
            if main_trade:
                ruleMatchPayment(main_trade)
                
        
        
        
        
        
        
