# -*- coding:utf8 -*-
import urllib 
import datetime
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.conf import settings

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions

from flashsale.pay.models import CustomShare,Customer
from flashsale.xiaolumm.models import XiaoluMama
from shopback.items.models import Product

from shopapp.weixin.models import WeixinUnionID
from shopapp.weixin.weixin_apis import WeiXinAPI,WeiXinRequestException
from . import permissions as perms
from . import serializers 
from shopback.base import log_action, ADDITION, CHANGE


class CustomShareViewSet(viewsets.ModelViewSet):
    """
    特卖分享API：
    
    - /today : (or /shop)分享店铺信息接口;
    - /product: 分享商品信息接口;
    > product_id:被分享的商品ID
    """
    queryset = CustomShare.objects.filter(status=True)
    serializer_class = serializers.CustomShareSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('该方法不被允许')
        
    def get_xlmm(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        if not customer.unionid.strip():
            return None
        xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
        return xiaolumms.count() > 0 and xiaolumms[0] or None
    
    def is_request_from_weixin(self,request):
        user_agent = request.META.get('HTTP_USER_AGENT')
        if user_agent and user_agent.find('MicroMessenger') > 0: 
            return True
        return False
    
    def get_xlmm_share_openid(self,xlmm):
        if not xlmm:
            return ''
        unoinid    = xlmm.openid
        wxunions    = WeixinUnionID.objects.filter(app_key=settings.WEIXIN_APPID,
                                                  unionid=unoinid)
        if not wxunions.exists():
            return ''
        return wxunions[0].openid
        
    def render_share_params(self, xlmm, cshare, product=None):
        if not cshare:
            return {'share_link':'',
                    'share_img':'',
                    'title':'',
                    'desc':'',
                    }
        xlmm_id  = xlmm and xlmm.id or 0
        serializer = self.get_serializer(cshare, many=False)
        resp     = serializer.data
        
        resp['share_link'] = cshare.share_link(xlmm=xlmm_id,product=product)
        resp['title']      = cshare.share_title(xlmm=xlmm_id,product=product)
        resp['desc']       = cshare.share_desc(xlmm=xlmm_id,product=product)
        resp['share_img']  = cshare.share_image(xlmm=xlmm_id,product=product)
        return resp
        
    @list_route(methods=['get'])
    def today(self, request, *args, **kwargs):
        """ 分享店铺信息接口 """
        
        xlmm     = self.get_xlmm(request)
        cshare = CustomShare.get_shop_share()
        resp = self.render_share_params(xlmm, cshare)
        
        if self.is_request_from_weixin(request):
            http_referer = request.META.get('HTTP_REFERER',settings.M_SITE_URL)
            referer_url  = request.GET.get('referer',http_referer).split('#')[0]
            resp['openid']     = self.get_xlmm_share_openid(xlmm)
            wx_api     = WeiXinAPI()
            signparams = wx_api.getShareSignParams(referer_url)
            resp['wx_singkey'] = signparams
            
        return Response(resp)
    
    shop = today
    
    @list_route(methods=['get'])
    def product(self, request, *args, **kwargs):
        """ 分享商品信息接口 """
        product_id = request.GET.get('product_id',0)
        product    = get_object_or_404(Product,id=product_id)
        
        xlmm     = self.get_xlmm(request)
        cshare = CustomShare.get_product_share()
        resp = self.render_share_params(xlmm, cshare, product=product)
        
        if self.is_request_from_weixin(request):
            http_referer = request.META.get('HTTP_REFERER',settings.M_SITE_URL)
            referer_url  = request.GET.get('referer',http_referer).split('#')[0]
            resp['openid']     = self.get_xlmm_share_openid(xlmm)
            wx_api     = WeiXinAPI()
            signparams = wx_api.getShareSignParams(referer_url)
            resp['wx_singkey'] = signparams

        return Response(resp)
