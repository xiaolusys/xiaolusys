#-*- coding:utf8 -*-
from .handler import BaseHandler
from shopback.trades.models import MergeTrade
from shopback import paramconfig as pcfg
from common.modelutils import  update_model_fields

class LogisticsHandler(BaseHandler):
    
    def handleable(self,merge_trade,*args,**kwargs):
        return (kwargs.get('first_pay_load',None) 
                or not merge_trade.logistics_company)
            
    def process(self,merge_trade,*args,**kwargs):
        
        state          = merge_trade.receiver_state
        city           = merge_trade.receiver_city
        district       = merge_trade.receiver_district
        shipping_type  = merge_trade.shipping_type.upper()
        
        from shopback.logistics.models import (Logistics,
                                               LogisticsCompany,
                                               DestCompany)
        
        try:
            if shipping_type == pcfg.EXPRESS_SHIPPING_TYPE.upper():
                        
                default_company =  LogisticsCompany.\
                                   get_recommend_express(
                                         receiver_state,
                                         receiver_city,
                                         receiver_district)
                                   
                merge_trade.logistics_company = default_company
                
            elif shipping_type in (pcfg.POST_SHIPPING_TYPE.upper(),
                                   pcfg.EMS_SHIPPING_TYPE.upper()):
                post_company = LogisticsCompany.objects.get(
                                            code=shipping_type)
                merge_trade.logistics_company = post_company
            
            update_model_fields(merge_trade,update_fields=
                                ['logistics_company'])
        
        except Exception,exc:
            merge_trade.append_reason_code(pcfg.DISTINCT_RULE_CODE)
        


