#-*- coding:utf8 -*-
import json
from django.http import HttpResponse
from django.db.models import Q
from djangorestframework.views import ModelView
from shopback.trades.models import MergeTrade,MergeOrder
from shopback.logistics.models import LogisticsCompany
from shopback.items.models import Product,ProductSku
from shopback.signals import rule_signal
from shopback import paramconfig as pcfg


class CheckOrderView(ModelView):
    """ docstring for class CheckOrderView """
    
    def get(self, request, id, *args, **kwargs):
        
        try:
            trade = MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            return {'code':0,'msg':'404,page not found'}
        
        logistics = LogisticsCompany.objects.filter(status=True)
        
        return {'trade':trade,'logistics':logistics}
        
    def post(self, request, id, *args, **kwargs):
        
        try:
            trade = MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            return {'code':0,'msg':'404,page not found'}
        
        priority = request.GET.get('priority')
        logistic_code = request.GET.get('logistic_code')
        
        params = {}
        if priority:
            params['priority'] = priority
        if logistic_code:
            params['logistics_company'] = LogisticsCompany.objects.get(code=logistic_code)
        if params:
            MergeTrade.objects.filter(id=id).update(params)

        check_msg = []
        if trade.has_refund:
            check_msg.append("有待退款")
        if trade.has_out_stock :
            check_msg.append("有缺货")
        if trade.has_rule_match:
            check_msg.append("信息不全")
        if trade.sys_status != pcfg.WAIT_AUDIT_STATUS:
            check_msg.append("订单暂不能审核")
        
        if check_msg:
            return {'code':0,'msg':'，'.join(check_msg)}
        
        rule_signal.send(sender='merge_trade_rule',trade_tid=trade.tid)
        
        MergeTrade.objects.filter(id=id,sys_status = pcfg.WAIT_AUDIT_STATUS)\
            .update(sys_status=pcfg.WAIT_PREPARE_SEND_STATUS,reason_code='')
        return {'code':1,'success':True}    
      
       
class OrderPlusView(ModelView):
    """ docstring for class OrderPlusView """
    
    def get(self, request, *args, **kwargs):
        
        q  = request.GET.get('q')
        if not q:
            return {'code':0,'msg':'没有输入查询关键字'}
        products = Product.objects.filter(Q(outer_id=q)|Q(name__contains=q))
        
        
    
    def post(self, request, *args, **kwargs):
        pass    
        
def change_trade_addr(request,id):
    
    try:
        trade = MergeTrade.objects.get(id=id)
    except MergeTrade.DoesNotExist:
        return {'code':0,'msg':'404,page not found'}
        
    CONTENT    = request.REQUEST
    for (key, val) in CONTENT.items():
         setattr(trade, key, val)
         
    trade.save()
    trade.append_reason_code(pcfg.ADDR_CHANGE_CODE)
    ret_params = {'code':1,'success':True}
    
    return HttpResponse(json.dumps(ret_params),mimetype="application/json")

    

        
       
        