#-*- encoding:utf8 -*-
import json
import time
import datetime
from django.conf import settings
from django.http import HttpResponse,Http404
from django.views.generic import View
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404

import pingpp
import logging
logger = logging.getLogger('django.request')

class PINGPPChargeView(View):
    
    def post(self, request, *args, **kwargs):
        
        content = request.body
        logger.debug('PINGPP CHARGE REQ: %s'%content)
        
        form = json.loads(content)
        form.update({ 'order_no':'T%s'%int(time.time()),
                      'app':dict(id=settings.PINGPP_APPID),
                      'currency':'cny',
                      'client_ip':'121.199.168.159',
                      'subject':'test-subject',
                      'body':'test-body',
                      'metadata':dict(color='red')})
        
        response_charge = pingpp.Charge.create(api_key=settings.PINGPP_APPKEY,**form)
        logger.debug('PINGPP CHARGE RESP: %s'%response_charge)
        
        return HttpResponse(json.dumps(response_charge),content_type='application/json')
    
    get = post
    

class PINGPPCallbackView(View):
    
    def post(self, request, *args, **kwargs):
        
        content = request.body 
        logger.debug('pingpp callback:%s'%content )
        return HttpResponse('ok',content_type='application/json')
    
    get = post
    
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer,TemplateHTMLRenderer
from rest_framework.views import APIView

from shopback.items.models import Product,ProductSku
from .serializes import ProductSerializer,ProductDetailSerializer

class ProductList(generics.ListCreateAPIView):
    
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    renderer_classes = (JSONRenderer,TemplateHTMLRenderer)
    
    template_name = "pay/mindex.html"
    #permission_classes = (permissions.IsAuthenticated,)
    
    def list(self, request, *args, **kwargs):
        
        content    = request.REQUEST
        time_line  = content.get('time_line','today')
        instance = self.filter_queryset(self.get_queryset())
        
        if time_line == "today":
            instance = instance.filter(sale_time=datetime.datetime(2015,3,28),
                                       status=Product.NORMAL)
        else:
            instance = instance.filter(sale_time=datetime.datetime(2015,3,29),
                                       status=Product.NORMAL)
        
        page = self.paginate_queryset(instance)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(instance, many=True)
            
        return Response(serializer.data)
    
    
class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    
    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    renderer_classes = (JSONRenderer,TemplateHTMLRenderer)
    
    template_name = "pay/mproduct.html"
    #permission_classes = (permissions.IsAuthenticated,)
    
    
class OrderBuyReview(APIView):

#     authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    template_name = "pay/morder.html"
    
    def post(self, request, format=None):
        
        content = request.REQUEST
        
        pid     = content.get('pid','')
        sid     = content.get('sid','')
        num     = int(content.get('num','1'))
        
        product = get_object_or_404(Product,pk=pid)
        sku  = get_object_or_404(ProductSku,pk=sid)
        if product.prod_skus.filter(id=sku.id).count() == 0:
            raise Http404
        #判断订单商品是否超出
        order_pass = False 
        product_dict = None
        sku_dict = None
        if num <= sku.realnum:
            order_pass =True
            product_dict = model_to_dict(product)
            sku_dict = model_to_dict(sku)
 
        post_fee = 0
        real_fee = num * sku.agent_price
        payment  = num * sku.agent_price + post_fee
        print num,real_fee,post_fee,payment,order_pass
        data = {'product':product_dict,
                'sku':sku_dict,
                'num':num,
                'real_fee':real_fee,
                'post_fee':post_fee,
                'payment':payment,
                'order_pass':order_pass}
        
        return Response(data)
    
    get = post

class OrderBuyConfirm(APIView):

#     authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    template_name = ""

    
    def post(self,  request, format=None):
        
        content = request.REQUEST
        
        pid = content.get('pid')
        sid  = content.get('sid')
        num   = int(content.get('num'))
        payment  = float(content.get('payment'))
        post_fee = float(content.get('post_fee'))
        
        
        product = get_object_or_404(Product,pk=pid)
        sku  = get_object_or_404(ProductSku,pk=sid)
        
        order_pass = False 
        product_dict = None
        sku_dict = None
        if num <= sku.realnum:
            order_pass =True
            product_dict = model_to_dict(product)
            sku_dict     = model_to_dict(sku)
            
            
        data = {'product':product_dict,
                'sku':sku_dict,
                'num':num,
                'post_fee':post_fee,
                'payment':payment,
                'order_pass':order_pass}
        
        return Response(data)
    
    get = post
    