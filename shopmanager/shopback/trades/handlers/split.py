#-*- coding:utf8 -*-
from django.conf import settings
from .handler import BaseHandler
from shopback.trades.models import MergeTrade
from shopapp.memorule import ruleMatchPayment,ruleMatchSplit
from shopback import paramconfig as pcfg
from common.modelutils import  update_model_fields

class SplitHandler(BaseHandler):
    """
        线上商品编码，内部商品编码映射,拆分，附赠品
    """
    def handleable(self,merge_trade,*args,**kwargs):
        return kwargs.get('first_pay_load',None) 
        
    def process(self,merge_trade,*args,**kwargs):
        
        if settings.DEBUG:
            print 'DEBUG COMPOSE:',merge_trade
            
        #组合拆分
        ruleMatchSplit(merge_trade)
        
        #金额匹配
        ruleMatchPayment(merge_trade)
        
            
            
            
            
            