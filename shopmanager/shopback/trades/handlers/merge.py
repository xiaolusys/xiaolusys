#-*- coding:utf8 -*-
from .handler import BaseHandler
from shopback.trades.models import MergeTrade
from shopback import paramconfig as pcfg
from common.modelutils import  update_model_fields

class LogisticsHandler(BaseHandler):
    
    def handleable(self,merge_trade,*args,**kwargs):
        return kwargs.get('first_pay_load',None) 
                
            
    def process(self,merge_trade,*args,**kwargs):
        pass
        
        
        
        