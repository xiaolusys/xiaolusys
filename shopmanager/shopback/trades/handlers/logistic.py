#-*- coding:utf8 -*-
from .handler import TradeHandler
from shopback.trades.models import MergeTrade
from shopback import paramconfig as pcfg
from common.modelutils import  update_model_fields

class LogisticsHandler(TradeHandler):
    
    def handleable(self):
        return self.first_pay_load or not self.merge_trade.logistics_company
            
    def process(self,*args,**kwargs):
        
        if not self.handleable():
            return 
        
        state          = self.merge_trade.receiver_state
        city           = self.merge_trade.receiver_city
        district       = self.merge_trade.receiver_district
        shipping_type  = self.merge_trade.shipping_type.upper()
        
        from shopback.logistics.models import Logistics,LogisticsCompany,DestCompany
        
        try:
            if shipping_type == pcfg.EXPRESS_SHIPPING_TYPE.upper():
                        
                default_company = LogisticsCompany.get_recommend_express(
                                                                         receiver_state,
                                                                         receiver_city,
                                                                         receiver_district)
                self.merge_trade.logistics_company = default_company
                
            elif shipping_type in (pcfg.POST_SHIPPING_TYPE.upper(),
                                           pcfg.EMS_SHIPPING_TYPE.upper()):
                post_company = LogisticsCompany.objects.get(code=shipping_type)
                self.merge_trade.logistics_company = post_company
                
            #如果订单选择使用韵达物流，则会请求韵达接口，查询订单是否到达，并做处理    
            if  self.merge_trade.logistics_company and \
                self.merge_trade.logistics_company.code == 'YUNDA':
                
                from shopapp.yunda.qrcode import select_order
                
                doc    = select_order([merge_trade.id])
                reach  = doc.xpath('/responses/response/reach')[0].text
                zonec  = doc.xpath('/responses/response/package_bm')[0].text
                zoned  = doc.xpath('/responses/response/package_mc')[0].text
                
                if reach == '0' or not reach:
                    self.merge_trade.sys_memo = u'韵达二维码不到'
                    self.merge_trade.logistics_company = LogisticsCompany.objects.get(code='YUNDA_QR')
                
                if reach == '1':
                    self.merge_trade.reserveo = zonec
                    self.merge_trade.reservet = zoned
            
            update_model_fields(self.merge_trade,update_fields=
                                                        ['logistics_company','reserveo','reservet','sys_memo'])
            
        except Exception,exc:
            merge_trade.append_reason_code(pcfg.DISTINCT_RULE_CODE)
        


