#-*- coding:utf8 -*-
import os
from django.conf import settings
from .handler import BaseHandler
from shopback.trades.models import MergeTrade,MergeBuyerTrade
from shopback import paramconfig as pcfg
from shopback.base import log_action,User, ADDITION, CHANGE
from common.modelutils import  update_model_fields

class RushHandler(BaseHandler):
    
    def getRushNameList(self):
        
        path = os.path.join(settings.PROJECT_ROOT,'fixtures','rush_trade_data.txt')
        with open(path,'rb') as f:
            return [s.strip() for s in f.readlines()]
    
    def handleable(self,merge_trade,*args,**kwargs):
        
        rush_set = set(self.getRushNameList()) 
        
        return kwargs.get('first_pay_load',None) and merge_trade.buyer_nick in rush_set
                
            
    def process(self,merge_trade,*args,**kwargs):
        
        if settings.DEBUG:
            print 'DEBUG RUSH:',merge_trade
            
        from shopback.logistics.models import LogisticsCompany
        lgc = LogisticsCompany.objects.get(code='HTKY')
        
        merge_trade.sys_memo += u'【汇通】'
        merge_trade.logistics_company = lgc
        update_model_fields(merge_trade,update_fields=['sys_memo','logistics_company'])
        
        