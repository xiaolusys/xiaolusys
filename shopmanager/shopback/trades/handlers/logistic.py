#-*- coding:utf8 -*-
from django.conf import settings
from .handler import BaseHandler
from shopback.trades.models import MergeTrade
from shopback import paramconfig as pcfg
from common.modelutils import  update_model_fields

class LogisticsHandler(BaseHandler):
    
    def handleable(self,merge_trade,*args,**kwargs):
        return (kwargs.get('first_pay_load',None) or 
                not merge_trade.logistics_company)
            
            
    def getLogisticCompany(self,merge_trade):
        
        from shopback.logistics.models import (Logistics,
                                               LogisticsCompany,
                                               DestCompany)
        if merge_trade.is_force_wlb:
            return LogisticCompany.objects.get_or_create(
                                    code=pcfg.WLB_LOGISTIC_CODE)
                    
        state          = merge_trade.receiver_state
        city           = merge_trade.receiver_city
        district       = merge_trade.receiver_district
        shipping_type  = merge_trade.shipping_type.upper()
                    
        if not state or not city or not district:
            raise Exception(u"地址不全(请精确到省市区（县）)")
                    
        if shipping_type == pcfg.EXPRESS_SHIPPING_TYPE.upper():
                        
            return LogisticsCompany.get_recommend_express(state,
                                                          city,
                                                          district)
                
        elif shipping_type in (pcfg.POST_SHIPPING_TYPE.upper(),
                               pcfg.EMS_SHIPPING_TYPE.upper()):
            return LogisticsCompany.objects.get_or_create(
                                        code=shipping_type)[0]
        
            
    def process(self,merge_trade,*args,**kwargs):
        
        if settings.DEBUG:
            print 'DEBUG LOGISTIC:',merge_trade
        
        try:
            if merge_trade.is_force_wlb:
                merge_trade.append_reason_code(pcfg.TRADE_BY_WLB_CODE)
             
            merge_trade.logistics_company = self.getLogisticCompany(merge_trade)
                 
            update_model_fields(merge_trade,update_fields=['logistics_company'])
        except Exception,exc:
            merge_trade.sys_memo += '[物流：%s]'%exc.message
            update_model_fields(merge_trade,update_fields=['sys_memo'])
            merge_trade.append_reason_code(pcfg.DISTINCT_RULE_CODE)
        


