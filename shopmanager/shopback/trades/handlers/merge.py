#-*- coding:utf8 -*-
from django.conf import settings
from .handler import BaseHandler
from shopback.trades.models import MergeTrade
from shopback import paramconfig as pcfg
from common.modelutils import  update_model_fields

class MergeHandler(BaseHandler):
    
    def handleable(self,merge_trade,*args,**kwargs):
        return (kwargs.get('first_pay_load',None) and 
                MergeTrade.objects.isTradeMergeable(merge_trade))
        
    def process(self,merge_trade,*args,**kwargs):
        
        if settings.DEBUG:
            print 'DEBUG MERGE:',merge_trade
            
        merge_trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
        
        if (MergeTrade.objects.isTradeRefunding(merge_trade) or 
            MergeTrade.objects.isTradeFullRefund(merge_trade)):
            return 
        
        main_trade = MergeTrade.objects.driveMergeTrade(merge_trade)
        if main_trade:
            rule_signal.send(sender='payment_rule',trade_id=main_trade.id)
            
            if not main_trade.reason_code and main_trade.sys_status == pcfg.WAIT_AUDIT_STATUS:
                main_trade.sys_status = pcfg.WAIT_PREPARE_SEND_STATUS
                update_model_fields(main_trade,update_fields=['sys_status'])
            
            merge_trade.remove_reason_code(pcfg.MULTIPLE_ORDERS_CODE)
            merge_trade.sys_status = pcfg.REGULAR_REMAIN_STATUS
            update_model_fields(merge_trade,update_fields=['sys_status'])
            
        
        
        
        
        
        