#-*- encoding:utf8 -*-
from django.conf import settings
from django.http import Http404,HttpResponseForbidden
from django.views.generic import View
from django.forms import model_to_dict
from django.shortcuts import redirect,get_object_or_404

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer,TemplateHTMLRenderer
from rest_framework.views import APIView

from .models import SaleTrade,SaleOrder,Customer,TradeCharge
from .models_refund import SaleRefund
from . import tasks
import pingpp
import logging
logger = logging.getLogger('django.request')

class RefundApply(APIView):
    
    renderer_classes = (JSONRenderer,TemplateHTMLRenderer)
#     permission_classes = (permissions.IsAuthenticated,)
    template_name = "pay/mrefundapply.html"
    
    def get(self, request, format=None):
        
        content  = request.GET
        user     = request.user
        customer = get_object_or_404(Customer,user=request.user)
        
        trade_id = content.get('trade_id')
        order_id = content.get('order_id')
        
        sale_order = get_object_or_404(SaleOrder,pk=order_id,sale_trade=trade_id,sale_trade__buyer_id=customer.id)
        
        if not sale_order.refundable:
            raise Http404
        
        if sale_order.refund:
            return redirect('refund_confirm',pk=sale_order.refund.id)

        return Response({'order':model_to_dict(sale_order)})
    
    def post(self, request, format=None):
        
        content  = request.POST
        user     = request.user
  
        trade_id = content.get('trade_id')
        order_id = content.get('order_id')
        return_good = content.get('return_good')
        
        customer = get_object_or_404(Customer,user=request.user)
        sale_trade = get_object_or_404(SaleTrade,pk=trade_id,buyer_id=customer.id)
        sale_order = get_object_or_404(SaleOrder,pk=order_id,sale_trade=trade_id,sale_trade__buyer_id=customer.id)
        
        if not sale_order.refundable:
            return HttpResponseForbidden('UNREFUNDABLE')
        
        if sale_order.refund:
            return redirect('refund_confirm',pk=sale_order.refund.id)
        
        params = {
                  'reason':content.get('reason'),
                  'refund_fee':content.get('refund_fee'),
                  'desc':content.get('desc'),
                  'trade_id':sale_trade.id,
                  'order_id':sale_order.id,
                  'buyer_nick':sale_trade.buyer_nick,
                  'item_id':sale_order.item_id,
                  'title':sale_order.title,
                  'sku_id':sale_order.sku_id,
                  'sku_name':sale_order.sku_name,
                  'total_fee':sale_order.total_fee,
                  'payment':sale_order.payment,
                  'mobile':sale_trade.receiver_mobile,
                  'phone':sale_trade.receiver_phone,
                  'charge':sale_trade.charge,
                  }
        if return_good:
            params.update({'refund_num':content.get('refund_num'),
                           'company_name':content.get('company_name'),
                           'sid':content.get('sid'),
                           'has_good_return':True,
                           'good_status':SaleRefund.BUYER_RECEIVED,
                           'status':SaleRefund.REFUND_WAIT_SELLER_AGREE
                           })
            
        else:
            good_status   = SaleRefund.BUYER_NOT_RECEIVED
            good_receive  = content.get('good_receive')
            if good_receive.lower() == 'y':
                good_status = SaleRefund.BUYER_RECEIVED
                
            params.update({'has_good_return':False,
                           'good_status':good_status,
                           'status':SaleRefund.REFUND_WAIT_SELLER_AGREE
                           })
        
        sale_refund = SaleRefund.objects.create(**params)
        
        try:
            so = SaleOrder.objects.get(id=order_id)
            so.refund_id  = sale_refund.id
            so.refund_fee = sale_refund.refund_fee
            so.refund_status  = sale_refund.refund_status
            so.save()
        except:
            pass
        
        if settings.DEBUG:
            tasks.pushTradeRefundTask(sale_refund.id)
        else:
            tasks.pushTradeRefundTask.s(sale_refund.id)()
        
        return Response(model_to_dict(sale_refund))
    
    
class RefundConfirm(APIView):
    
    renderer_classes = (JSONRenderer,TemplateHTMLRenderer)
#     permission_classes = (permissions.IsAuthenticated,)
    template_name = "pay/mrefundconfirm.html"
    
    def get(self, request, pk, format=None):
        
        customer = get_object_or_404(Customer,user=request.user)
        sale_refund = get_object_or_404(SaleRefund,pk=pk)
        sale_order  = get_object_or_404(SaleOrder,pk=sale_refund.order_id,
                                        sale_trade=sale_refund.trade_id,
                                        sale_trade__buyer_id=customer.id)
        
        refund_dict = model_to_dict(sale_refund)
        refund_dict.update({'created':sale_refund.created,
                            'modified':sale_refund.modified})

        return Response({'order':model_to_dict(sale_order),
                         'refund':refund_dict})
    
    def post(self, request, pk, format=None):
        
        return Response({})
    
    
    
    