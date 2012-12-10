#-*- coding:utf8 -*-
import json
from django.http import HttpResponse
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from djangorestframework.views import ModelView
from djangorestframework.response import ErrorResponse
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
            raise ErrorResponse('该订单不存在'.decode('utf8'))
        
        logistics = LogisticsCompany.objects.filter(status=True)
        
        trade_dict = {
            'id':trade.id,
            'tid':trade.tid,
            'buyer_nick':trade.buyer_nick,
            'seller_nick':trade.seller_nick,
            'pay_time':trade.pay_time,
            'buyer_message':trade.buyer_message,
            'seller_memo':trade.seller_memo,
            'logistics_company':trade.logistics_company,
            'priority':trade.priority,
            'receiver_name':trade.receiver_name,
            'receiver_state':trade.receiver_state,
            'receiver_city':trade.receiver_city,
            'receiver_district':trade.receiver_district,
            'receiver_address':trade.receiver_address,
            'receiver_mobile':trade.receiver_mobile,
            'receiver_phone':trade.receiver_phone,
            'has_memo':trade.has_memo,
            'has_refund':trade.has_refund,
            'has_out_stock':trade.has_out_stock,
            'has_rule_match':trade.has_rule_match,
            'has_merge':trade.has_merge,
            'status':trade.status,
            'sys_status':trade.sys_status,
            'used_orders':trade.inuse_orders,
        }

        return {'trade':trade_dict,'logistics':logistics}
        
    def post(self, request, id, *args, **kwargs):
        
        try:
            trade = MergeTrade.objects.get(id=id)
        except MergeTrade.DoesNotExist:
            raise ErrorResponse('该订单不存在'.decode('utf8'))
        
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
            check_msg.append("有待退款".decode('utf8'))
        if trade.has_out_stock :
            check_msg.append("有缺货".decode('utf8'))
        if trade.has_rule_match:
            check_msg.append("信息不全".decode('utf8'))
        if trade.sys_status != pcfg.WAIT_AUDIT_STATUS:
            check_msg.append("订单暂不能审核".decode('utf8'))
            
        if check_msg:
            raise ErrorResponse('，'.join(check_msg))

        rule_signal.send(sender='merge_trade_rule',trade_tid=trade.tid)
        
        MergeTrade.objects.filter(id=id,sys_status = pcfg.WAIT_AUDIT_STATUS)\
            .update(sys_status=pcfg.WAIT_PREPARE_SEND_STATUS,reason_code='')
        return {'success':True}    
      
       
class OrderPlusView(ModelView):
    """ docstring for class OrderPlusView """
    
    def get(self, request, *args, **kwargs):
        
        q  = request.GET.get('q')
        if not q:
            raise ErrorResponse('没有输入查询关键字'.decode('utf8'))
        products = Product.objects.filter(Q(outer_id=q)|Q(name__contains=q))
        
        prod_list = [(prod.outer_id,prod.name,[[(sku.outer_id,sku.properties_name) for sku in 
                                                prod.prod_skus.filter(status=pcfg.NORMAL) ]]) for prod in products]
        return prod_list
        
    def post(self, request, *args, **kwargs):
        
        trade_id = request.POST.get('trade_id')
        outer_id = request.POST.get('outer_id')
        outer_sku_id = request.POST.get('outer_sku_id')
        num      = request.POST.get('num',1)    
        
        try:
            merge_trade = MergeTrade.objects.get(id=trade_id)
        except MergeTrade.DoesNotExist:
            raise ErrorResponse('该订单不存在'.decode('utf8'))
        try:
            product = Product.objects.get(outer_id=outer_id)
        except Product.DoesNotExist:
            raise ErrorResponse('该商品不存在'.decode('utf8'))
        
        if outer_sku_id:
            try:
                prod_sku = ProductSku.objects.get(prod_outer_id=outer_sku_id)
            except ProductSku.DoesNotExist:
                raise ErrorResponse('该商品规格不存在'.decode('utf8'))
            
        merge_order = MergeOrder.gen_new_order(trade_id,outer_id,outer_sku_id,num,gift_type=pcfg.CS_PERMI_GIT_TYPE)
        
        return merge_order
    
    
class ProdSkuPlusView(ModelView):
    """ docstring for class SkuPlusView """
    
    def get(self, request, *args, **kwargs):
        
        outer_id = request.GET.get('outer_id')
        try:
            prod = Product.objects.get(outer_id=outer_id)
        except Product.DoesNotExsit:
            raise ErrorResponse('商品不存在'.decode('utf8'))
        
        return (prod.outer_id,prod.name,[[(sku.outer_id,sku.properties_name) for sku in 
                                                prod.prod_skus.filter(status=pcfg.NORMAL)]])
        
    def post(self, request, *args, **kwargs):
        pass
        
@csrf_exempt     
def change_trade_addr(request):
    
    CONTENT    = request.REQUEST
    trade_id   = CONTENT.get('trade_id')
    try:
        trade = MergeTrade.objects.get(id=trade_id)
    except MergeTrade.DoesNotExist:
        raise ErrorResponse('该订单不存在'.decode('utf8'))
        
    for (key, val) in CONTENT.items():
         setattr(trade, key, val)
         
    trade.save()
    trade.append_reason_code(pcfg.ADDR_CHANGE_CODE)
    ret_params = {'code':0,'success':True}
    
    return HttpResponse(json.dumps(ret_params),mimetype="application/json")

    

        
       
        