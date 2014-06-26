#-*- coding:utf8 -*-
from django.conf import settings
from .handler import BaseHandler
from shopback.trades.models import MergeTrade
from shopback import paramconfig as pcfg
from shopapp.memorule import ruleMatchPayment
from common.modelutils import  update_model_fields

class MergeHandler(BaseHandler):
    
    def handleable(self,merge_trade,*args,**kwargs):
        return (kwargs.get('first_pay_load',None) and 
                MergeTrade.objects.isTradeMergeable(merge_trade))
        
    def process(self,merge_trade,*args,**kwargs):
        
        if settings.DEBUG:
            print 'DEBUG MERGE:',merge_trade
            
        merge_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
        
        main_trade = MergeTrade.objects.driveMergeTrade(merge_trade)
        if main_trade:
            ruleMatchPayment(main_trade)
            
        
        
        
        
        
        