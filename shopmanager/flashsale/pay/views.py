#-*- encoding:utf8 -*-
import json
import time
import datetime
from django.conf import settings
from django.db import IntegrityError,models
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
    
    def createSaleTrade(self,customer,form):
        uuid = form.get('uuid')
        if not UUID_RE.match(uuid):
            raise Exception('参数错误!')
        
        product = Product.objects.get(pk=form.get('item_id'))
        sku = ProductSku.objects.get(pk=form.get('sku_id'),product=product)
        total_fee = sku.std_sale_price * int(form.get('num'))
        
        sale_trade = SaleTrade.objects.create(
                                 tid=uuid,
                                 buyer_id=customer.id,
                                 channel=form.get('channel'),
                                 receiver_name=form.get('receiver_name'),
                                 receiver_state=form.get('receiver_state'),
                                 receiver_city=form.get('receiver_city'),
                                 receiver_district=form.get('receiver_district'),
                                 receiver_address=form.get('receiver_address'),
                                 receiver_zip=form.get('receiver_zip'),
                                 receiver_phone=form.get('receiver_phone',''),
                                 receiver_mobile=form.get('receiver_mobile'),
                                 buyer_message=form.get('buyer_message',''),
                                 payment=float(form.get('payment')),
                                 total_fee=total_fee,
                                 post_fee=form.get('post_fee'),
                                 status=SaleTrade.WAIT_BUYER_PAY
                                 )

        SaleOrder.objects.create(oid=uuid,
                                 sale_trade=sale_trade,
                                 item_id=form.get('item_id'),
                                 sku_id=form.get('sku_id'),
                                 num=form.get('num'),
                                 outer_id=product.outer_id,
                                 outer_sku_id=sku.outer_id,
                                 title=product.name,
                                 payment=float(form.get('payment')),
                                 total_fee=total_fee,
                                 pic_path=product.pic_path,
                                 sku_name=sku.properties_alias,
                                 status=SaleTrade.WAIT_BUYER_PAY)
        
        return sale_trade
    
    def post(self, request, *args, **kwargs):
        
        form = request.POST
        logger.debug('PINGPP CHARGE REQ: %s'%form)
        err_msg = ''
        try:
            
            channel = form.get('channel')
            user = request.user
            customer = Customer.getCustomerByUser(user)
            if not customer:
                raise Exception(u'用户未找到')
            
            strade = self.createSaleTrade(customer,form)
            
            if channel == SaleTrade.WX_PUB:
                extra = {'open_id':customer.openid,'trade_type':'JSAPI'}
                
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
                      'client_ip':settings.PINGPP_CLENTIP,
                      'subject':u'小鹿美美平台交易',
                      'body':strade.body_describe,
                      'metadata':dict(color='red'),
                      'extra':extra}
            
            response_charge = pingpp.Charge.create(api_key=settings.PINGPP_APPKEY,**params)
        
        except IntegrityError:
            err_msg = u'订单已提交'
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            err_msg = u'参数错误'
            
        if err_msg:
            response_charge = {'errcode':'10001','errmsg':err_msg}
        
        logger.debug('CHARGE RESP: %s'%response_charge)
        
        return HttpResponse(json.dumps(response_charge),content_type='application/json')
    
    get = post
    

from . import tasks

class PINGPPCallbackView(View):
    
    def post(self, request, *args, **kwargs):
        
        content = request.body 
        logger.debug('pingpp callback:%s'%content )

        # 读取异步通知数据
        notify   = json.loads(content)
        response = ''
        
        # 对异步通知做处理
        if 'object' not in notify:
            response = 'fail'
        else:
            if notify['object'] == 'charge':
                # 开发者在此处加入对支付异步通知的处理代码
                if settings.DEBUG:
                    tasks.notifyTradePayTask(notify)
                else:
                    tasks.notifyTradePayTask.s(notify)()
                
                response = 'success'
            elif notify['object'] == 'refund':
                # 开发者在此处加入对退款异步通知的处理代码
                if settings.DEBUG:
                    tasks.notifyTradeRefundTask(notify)
                else:
                    tasks.notifyTradeRefundTask.s(notify)()
                
                response = 'success'
            else:
                response = 'fail'
        
        return HttpResponse(response)
    
    get = post
    
    
class WXPayWarnView(View):
    
    def post(self, request, *args, **kwargs):
        
        content = request.body
        logger.error('wx warning:%s'%content )
        return HttpResponse('ok')
    
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
    paginate_by = 10
    
    def list(self, request, *args, **kwargs):
        
        content    = request.REQUEST
        time_line  = content.get('time_line','0')
        if not time_line.isdigit() or int(time_line) < 0:
            time_line = 0
        time_line = int(time_line)
        
        filter_date = datetime.datetime.now() + datetime.timedelta(days=time_line)
        
        instance = self.filter_queryset(self.get_queryset())

        instance = instance.filter(sale_time=filter_date.date(),status=Product.NORMAL)

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

import urllib
from .models_addr import UserAddress
from .views_address import ADDRESS_PARAM_KEY_NAME
from .options import getAddressByUserOrID
from django.http import HttpResponseForbidden

class OrderBuyReview(APIView):

#     authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    template_name = "pay/morder.html"
    
    def post(self, request, format=None):
        
        content = request.REQUEST
        user    = request.user
        
        pid     = content.get('pid','')
        sid     = content.get('sid','')
        num     = int(content.get('num','1'))
        addrid  = content.get(ADDRESS_PARAM_KEY_NAME,'')
        
        product = get_object_or_404(Product,pk=pid)
        sku  = get_object_or_404(ProductSku,pk=sid)
        if product.prod_skus.filter(id=sku.id).count() == 0:
            raise Http404
        
        #判断订单商品是否超出
        order_pass = False 
        product_dict = {}
        sku_dict = {}

        if num <= sku.realnum:
            order_pass =True
            product_dict = model_to_dict(product)
            sku_dict     = model_to_dict(sku)
 
        post_fee = 0
        real_fee = num * sku.agent_price
        payment  = num * sku.agent_price + post_fee
        
        customers = Customer.objects.filter(user=user)
        if customers.count() < 0:
            raise HttpResponseForbidden('NOT EXIST')
        
        address = getAddressByUserOrID(customers[0],addrid)
        if address:
            address = model_to_dict(address)
        
        abs_url  = request.build_absolute_uri().split('#')[0]
        urlparam = urllib.urlencode({'url':abs_url})
        origin_url = urlparam[len('url='):]
     
        data = {'product':product_dict,
                'sku':sku_dict,
                'num':num,
                'uuid':genUUID(),
                'real_fee':real_fee,
                'post_fee':post_fee,
                'payment':payment,
                'address':address,
                'origin_url':origin_url,
                'order_pass':order_pass}
        
        return Response(data)
    
    get = post
    
    
class MyOrderList(APIView):
    
    permission_classes = (permissions.IsAuthenticated,)
    template_name = "pay/myorder.html"
    
    def get(self, request, format=None):
        
        return Response({})
    
    def post(self, request, format=None):
        
        return Response({})
    
    