#-*- encoding:utf8 -*-
import json
import time
import datetime
from django.conf import settings
from django.http import HttpResponse,Http404
from django.views.generic import View
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404

from shopback.items.models import Product,ProductSku
from .models import SaleTrade,SaleOrder,genUUID,Customer
import pingpp
import logging
logger = logging.getLogger('django.request')

import re
UUID_RE = re.compile('^[a-f0-9-]{36}$')

class PINGPPChargeView(View):
    
    def createSaleTrade(self,form):
        uuid = form.pop('uuid')
        if not UUID_RE.match(uuid):
            raise Http404('UUID NOT EXIST')
        
        sale_trade = SaleTrade.objects.create(
                                 tid=uuid,
                                 buyer_id=form.get('buyer_id'),
                                 channel=form.get('channel'),
                                 receiver_name=form.get('receiver_name'),
                                 receiver_state=form.get('receiver_state'),
                                 receiver_address=form.get('receiver_address'),
                                 receiver_phone=form.get('receiver_phone'),
                                 buyer_message=form.get('buyer_message'),
                                 payment=float(form.get('payment')),
                                 post_fee=form.get('post_fee'),
                                 status=SaleTrade.WAIT_BUYER_PAY
                                 )
        
        product = get_object_or_404(Product,pk=form.get('item_id'))
        sku = get_object_or_404(ProductSku,pk=form.get('sku_id'))
        
        SaleOrder.objects.create(oid=uuid,
                                 sale_trade=sale_trade,
                                 item_id=form.get('item_id'),
                                 sku_id=form.get('sku_id'),
                                 num=form.get('num'),
                                 outer_id=product.outer_id,
                                 outer_sku_id=sku.outer_id,
                                 title=product.name,
                                 pic_path=product.pic_path,
                                 sku_name=sku.properties_alias,
                                 status=SaleTrade.WAIT_BUYER_PAY)
        
        return sale_trade
    
    def post(self, request, *args, **kwargs):
        
        content = request.body
        logger.debug('PINGPP CHARGE REQ: %s'%content)
        
        form = json.loads(content)
        channel = form.get('channel')
        
        customer = Customer.getCustomerByUser(request.user)
        form.update(buyer_id=customer.id)
        
        strade = self.createSaleTrade(form)
        
        if channel == SaleTrade.WX_PUB:
            extra = {'open_id':customer.openid,
                    'trade_type':'JSAPI'}
            
        elif channel == SaleTrade.ALIPAY_WAP:
            extra = {"success_url":"%s/mm/callback/"%settings.SITE_URL,
                     "cancel_url":"%s/mm/cancel/"%settings.SITE_URL}
            
        elif channel == SaleTrade.UPMP_WAP:
            extra = {"result_url":"%s/mm/callback/?code="%settings.SITE_URL}
        
        params ={ 'order_no':'T%s'%strade.id,
                  'app':dict(id=settings.PINGPP_APPID),
                  'channel':channel,
                  'currency':'cny',
                  'amount':'%d'%(strade.payment*100),
                  'client_ip':'121.199.168.159',
                  'subject':u'小鹿美美平台交易',
                  'body':strade.body_describe,
                  'metadata':dict(color='red'),
                  'extra':extra}
        
        response_charge = pingpp.Charge.create(api_key=settings.PINGPP_APPKEY,**params)
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

        data = {'product':product_dict,
                'sku':sku_dict,
                'num':num,
                'uuid':genUUID(),
                'real_fee':real_fee,
                'post_fee':post_fee,
                'payment':payment,
                'order_pass':order_pass}
        
        return Response(data)
    
    get = post
    
    


    