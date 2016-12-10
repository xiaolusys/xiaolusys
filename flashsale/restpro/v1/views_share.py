# -*- coding:utf8 -*-
import urllib
import datetime
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.conf import settings
from django.core.cache import cache

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions
from rest_framework.views import APIView

from flashsale.pay.models import CustomShare, Customer, ModelProduct
from flashsale.xiaolumm.models import XiaoluMama
from shopback.items.models import Product
from common.urlutils import replace_domain

from shopapp.weixin.models import WeixinUnionID
from shopapp.weixin.apis import WeiXinAPI, WeiXinRequestException
from flashsale.restpro import permissions as perms
from . import serializers
from core.options import log_action, ADDITION, CHANGE


class CustomShareViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ### 特卖分享API：
    > ### /weixin_signs :获取微信分享签名;
    > ### /shop :分享店铺信息接口;
    > ### /product: 分享商品信息接口;
    - product_id:被分享的商品ID
    > ### /model: 分享商品款式信息接口;
    - model_id:被分享的商品款式ID
    """
    queryset = CustomShare.objects.filter(status=True)
    serializer_class = serializers.CustomShareSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # permission_classes = (permissions.IsAuthenticated,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    _xlmm = None

    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('该方法不被允许')

    def get_xlmm(self, request):
        if self._xlmm:
            return self._xlmm
        if not request.user or request.user.is_anonymous():
            return None
        customer = Customer.objects.normal_customer.filter(user_id=request.user.id).first()
        if not customer or not customer.unionid.strip():
            return None
        xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
        self._xlmm = xiaolumms.first()
        return self._xlmm

    def is_request_from_weixin(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT')
        if user_agent and user_agent.find('MicroMessenger') > 0:
            return True
        return False

    def get_xlmm_share_openid(self, xlmm):
        if not xlmm:
            return ''
        unoinid = xlmm.openid
        wxunions = WeixinUnionID.objects.filter(app_key=settings.WEIXIN_APPID,
                                                unionid=unoinid)
        if not wxunions.exists():
            return ''
        return wxunions[0].openid

    def render_share_params(self, xlmm, cshare, **kwargs):
        if not cshare:
            return {'share_link': '',
                    'share_img': '',
                    'title': '',
                    'desc': '',}
        xlmm_id = xlmm and xlmm.id or 0
        serializer = self.get_serializer(cshare, many=False)
        resp = serializer.data

        product = kwargs.get('product', None)
        if product:
            product.detail_note = product.detail and product.detail.note or ''

        resp['share_link'] = replace_domain(cshare.share_link(xlmm=xlmm_id, **kwargs))
        resp['title'] = cshare.share_title(xlmm=xlmm_id, **kwargs)
        resp['desc'] = cshare.share_desc(xlmm=xlmm_id, **kwargs)
        resp['share_img'] = cshare.share_image(xlmm=xlmm_id, **kwargs)
        return resp

    def affix_weixin_share_param(self, request):
        """ 生成微信分享参数 """
        xlmm = self.get_xlmm(request)
        http_referer = request.META.get('HTTP_REFERER', settings.M_SITE_URL)
        referer_url = request.GET.get('referer', http_referer).split('#')[0]

        wx_api = WeiXinAPI(appKey=settings.WX_PUB_APPID)
        signparams = wx_api.getShareSignParams(referer_url)

        return {'openid': self.get_xlmm_share_openid(xlmm),
                'wx_singkey': signparams}

    @list_route(methods=['get'])
    def weixin_signs(self, request, *args, **kwargs):

        http_referer = request.META.get('HTTP_REFERER', settings.M_SITE_URL)
        referer_url = request.GET.get('referer', http_referer).split('#')[0]

        wx_api = WeiXinAPI(appKey=settings.WX_PUB_APPID)
        cache_signs = wx_api.getShareSignParams(referer_url)

        return Response(cache_signs)


    @list_route(methods=['get'])
    def today(self, request, *args, **kwargs):
        """ 分享店铺信息接口 """

        xlmm = self.get_xlmm(request)
        cshare = CustomShare.get_instance_by_type(CustomShare.SHOP_SHARE)
        resp = self.render_share_params(xlmm, cshare)

        if self.is_request_from_weixin(request):
            wxshare_params = self.affix_weixin_share_param(request)
            resp.update(wxshare_params)

        return Response(resp)

    shop = today

    @list_route(methods=['get'])
    def product(self, request, *args, **kwargs):
        """ 分享商品信息接口 """
        product_id = request.GET.get('product_id', '0')
        if product_id and not product_id.isdigit():
            product_id = product_id.split('?')[0].split('/')[-1]
        product = get_object_or_404(Product, id=product_id)

        xlmm = self.get_xlmm(request)
        cshare = CustomShare.get_instance_by_type(CustomShare.PRODUCT_SHARE)
        resp = self.render_share_params(xlmm, cshare, product=product)

        if self.is_request_from_weixin(request):
            wxshare_params = self.affix_weixin_share_param(request)
            resp.update(wxshare_params)

        return Response(resp)

    @list_route(methods=['get'])
    def model(self, request, *args, **kwargs):
        """ 分享商品款式信息接口 """
        model_id = request.GET.get('model_id', '0')
        if model_id and not model_id.isdigit():
            model_id = model_id.split('?')[0].split('/')[-1]
        product_model = get_object_or_404(ModelProduct, id=model_id)

        xlmm = self.get_xlmm(request)
        cshare = CustomShare.get_instance_by_type(CustomShare.MODEL_SHARE)
        resp = self.render_share_params(xlmm, cshare, model=product_model)

        if self.is_request_from_weixin(request):
            wxshare_params = self.affix_weixin_share_param(request)
            resp.update(wxshare_params)

        return Response(resp)
