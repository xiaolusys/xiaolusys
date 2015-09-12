#-*- coding:utf8 -*-
from django.conf import settings
from .handler import BaseHandler
from shopback.trades.models import MergeTrade
from shopback.items.models import Product
from shopback import paramconfig as pcfg
from common.modelutils import  update_model_fields
from shopback.logistics.models import (LogisticsCompany,
                                       DestCompany)

class LogisticsHandler(BaseHandler):
    def handleable(self, merge_trade, *args, **kwargs):
        return (kwargs.get('first_pay_load', None) or
                not merge_trade.logistics_company or kwargs.get('update_logistic', None))
            
    def getYundaLGC(self):
        return LogisticsCompany.objects.get_or_create(code='YUNDA_QR')[0]
    
    def getLogisticCompany(self,merge_trade):
        
        if merge_trade.is_force_wlb:
            return LogisticsCompany.objects.get_or_create(
                                    code=pcfg.WLB_LOGISTIC_CODE)
                    
        state          = merge_trade.receiver_state
        city           = merge_trade.receiver_city
        district       = merge_trade.receiver_district
        shipping_type  = merge_trade.shipping_type.upper()
                    
        if not state or not city or not district:
            raise Exception(u"地址不全(请精确到省市区（县）)")
                    
        if shipping_type == pcfg.EXPRESS_SHIPPING_TYPE.upper():
            #定制订单快递分配
            if (merge_trade.receiver_address.find(u'镇') >= 0 
                and merge_trade.receiver_address.find(u'村') >= 0):
                states = (u'甘肃',u'青海',u'陕西',u'广西',u'宁夏',u'贵州',u'内蒙',u'西藏',u'新疆')
                if state.startswith(states):
                    return LogisticsCompany.objects.get_or_create(
                                        code='POSTB')[0]
                return LogisticsCompany.objects.get_or_create(
                                        code='STO')[0]
            
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
            #如果订单属于广州仓，则默认发韵达
            if merge_trade.ware_by == MergeTrade.WARE_GZ:
                merge_trade.logistics_company = self.getYundaLGC()
            else:
                merge_trade.logistics_company = self.getLogisticCompany(merge_trade)
            update_model_fields(merge_trade,update_fields=['logistics_company','ware_by'])
            
            if merge_trade.ware_by == MergeTrade.WARE_NONE:
                raise Exception(u'请拆单或选择始发仓')
        except Exception,exc:
            merge_trade.sys_memo += u'[物流：%s]'%exc.message
            update_model_fields(merge_trade,update_fields=['sys_memo'])
            merge_trade.append_reason_code(pcfg.DISTINCT_RULE_CODE)
        


