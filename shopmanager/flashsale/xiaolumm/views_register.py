#-*- coding:utf-8 -*-

import json
import datetime
import urllib
import urlparse
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse,Http404
from django.shortcuts import redirect,render_to_response,get_object_or_404
from django.views.generic import View
from django.template import RequestContext
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers 
from rest_framework.response import Response
from rest_framework import exceptions

from core.weixin.mixins import WeixinAuthMixin

from flashsale.pay.options import get_user_unionid,valid_openid
from flashsale.pay.mixins import PayInfoMethodMixin
from flashsale.pay.models import Customer, SaleTrade, SaleOrder
from shopback.items.models import ProductSku
from flashsale.xiaolumm.models import XiaoluMama
from shopapp.weixin.models import WeiXinUser
from shopback.items.models import Product

import logging
logger = logging.getLogger('django.request')

class MamaRegisterView(WeixinAuthMixin,PayInfoMethodMixin,APIView):
    """ 小鹿妈妈申请成为代理 """
#     authentication_classes = (authentication.TokenAuthentication,)
#     permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "apply/mama_profile.html"
    
    def get(self, request, mama_id):
        openid,unionid = self.get_openid_and_unionid(request)
        if not valid_openid(openid) or not valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)
        
        wx_user,state = WeiXinUser.objects.get_or_create(openid=openid)
        try:
            xiaolumm = XiaoluMama.objects.get(openid=unionid)
        except XiaoluMama.DoesNotExist: 
            response = Response({
                        'openid':openid,
                        'unionid':unionid,
                        'wxuser':wx_user,
                    })
            self.set_cookie_openid_and_unionid(response, openid, unionid)
            return response
            
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            raise exc

        if xiaolumm.progress == XiaoluMama.NONE:
            response = Response({
                        'openid':openid,
                        'unionid':unionid,
                        'wxuser':wx_user,
                    })
            self.set_cookie_openid_and_unionid(response, openid, unionid)
            return response
        
        elif xiaolumm.need_pay_deposite():
            return redirect(reverse('mama_deposite',kwargs={'mama_id':mama_id}))
        
        else:
            return redirect(reverse('mama_homepage'))
        

            
            
    def post(self,request, mama_id):
        content = request.REQUEST
        openid  = content.get('openid')
        unionid = content.get('unionid')
#         nickname  = content.get('nickname')

        wx_user = get_object_or_404(WeiXinUser,openid=openid)
        if not wx_user.isValid() or not valid_openid(unionid):#or not nickname
            return redirect('./')
        
        xlmm, state = XiaoluMama.objects.get_or_create(openid=unionid)
        parent_mobile = xlmm.referal_from
        if int(mama_id) > 0 and not parent_mobile:
            parent_xlmm = get_object_or_404(XiaoluMama,id=mama_id)
            parent_mobile = parent_xlmm.mobile
            
        xlmm.progress = XiaoluMama.PROFILE
#         xlmm.referal_from = parent_mobile
        xlmm.save()
        
        return redirect(reverse('mama_deposite',kwargs={'mama_id':mama_id}))


class PayDepositeView(PayInfoMethodMixin, APIView):
    """ 小鹿妈妈支付押金 """
#     authentication_classes = (authentication.TokenAuthentication,)
#     permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer,renderers.TemplateHTMLRenderer)
    template_name = 'apply/mama_deposit.html'
    
    def get_deposite_product(self):
        return Product.objects.get(id=2731)
    
    def get_full_link(self,link):
        return urlparse.urljoin(settings.M_SITE_URL, link)
    
    def get(self, request, mama_id):
        xlmm = self.get_xiaolumm(request)
        if not xlmm:
            return redirect(reverse('mama_register',kwargs={'mama_id':mama_id}))
        
        if not xlmm.need_pay_deposite():
            return redirect(reverse('mama_homepage'))
        
        product = self.get_deposite_product()
        deposite_params = self.calc_deposite_amount_params(request, product)
        return Response({
            'uuid':self.get_trade_uuid(),
            'xlmm':xlmm,
            'product':product,
            'payinfos':deposite_params,
            'referal_mamaid':mama_id,
            'success_url':self.get_full_link(reverse('mama_registerok')),
            'cancel_url':self.get_full_link(reverse('mama_registerfail'))
        })
        
    def post(self, request, *args, **kwargs):
        CONTENT  = request.REQUEST.copy()
        item_id  = CONTENT.get('item_id')
        sku_id   = CONTENT.get('sku_id')
        sku_num  = int(CONTENT.get('num','1'))
        
        customer = get_object_or_404(Customer,user=request.user)
        product         = get_object_or_404(Product,id=item_id)
        product_sku     = get_object_or_404(ProductSku,id=sku_id)
        payment         = int(float(CONTENT.get('payment','0')) * 100)
        post_fee        = int(float(CONTENT.get('post_fee','0')) * 100)
        discount_fee    = int(float(CONTENT.get('discount_fee','0')) * 100)
        bn_totalfee     = int(product_sku.agent_price * sku_num * 100)
        
        if product_sku.free_num < sku_num or product.shelf_status == Product.DOWN_SHELF:
            raise exceptions.ParseError(u'商品已被抢光啦！')
        
        bn_payment      = bn_totalfee + post_fee - discount_fee
        if post_fee < 0 or payment <= 0 or abs(payment - bn_payment) > 10 :
            raise exceptions.ParseError(u'付款金额异常')
#         addr_id  = CONTENT.get('addr_id')
#         address  = get_object_or_404(UserAddress,id=addr_id,cus_uid=customer.id)
        address  = None
        channel  = CONTENT.get('channel')
        if channel not in dict(SaleTrade.CHANNEL_CHOICES):
            raise exceptions.ParseError(u'付款方式有误')
        
        try:
            lock_success =  Product.objects.lockQuantity(product_sku,sku_num)
            if not lock_success:
                raise exceptions.APIException(u'商品库存不足')
            sale_trade, state = self.create_deposite_trade(CONTENT, address, customer)
            if state:
                self.create_SaleOrder_By_Productsku(sale_trade, product, product_sku, sku_num)
        except exceptions.APIException,exc:
            raise exc
        
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            Product.objects.releaseLockQuantity(product_sku, sku_num)
            raise exceptions.APIException(u'订单生成异常')
        
        response_charge = self.pingpp_charge(sale_trade,**CONTENT)
        
        return Response(response_charge)
        
        
class MamaSuccessView(APIView):
    
#     authentication_classes = (authentication.TokenAuthentication,)
#     permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "apply/mama_success.html"
        
    def get(self,request):
        response = {}
        return Response(response)
    
class MamaFailView(APIView):
    
#     authentication_classes = (authentication.TokenAuthentication,)
#     permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "apply/mama_fail.html"
        
    def get(self,request):
        response = {'mama_id':request.REQUEST.get('mama_id')}
        return Response(response)
    
     
