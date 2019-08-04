# -*- coding:utf-8 -*-

import logging
import re
import urlparse

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404

from rest_framework import authentication
from rest_framework import exceptions
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.views import APIView

from core.weixin.mixins import WeixinAuthMixin
from flashsale.pay.mixins import PayInfoMethodMixin
from flashsale.pay.models import Customer, SaleTrade
from flashsale.xiaolumm.models import XiaoluMama
from shopapp.weixin.options import get_openid_by_unionid
from shopback.items.models import Product
from flashsale.pay.models import ProductSku

logger = logging.getLogger(__name__)


class BitMallView(WeixinAuthMixin, APIView):
    """ 比特优品申请成为代理 """
    authentication_classes = (authentication.SessionAuthentication,)
    # permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "bitmall/step-1.html"

    def get(self, request):
        """
        mama_id: 推荐人的专属id
        """
        content = request.GET
        mama_id = content.get('mama_id')
        # mama_id = re.match("\d+",mama_id).group()

        response = Response({
            'openid': None,
            'unionid': None,
            'xiaolumm': None,
            "mama_id": mama_id
        })
        # self.set_cookie_openid_and_unionid(response, openid, unionid)
        return response


class BitMallRegisterView(WeixinAuthMixin, PayInfoMethodMixin, APIView):
    """ 比特优品申请成为代理 """
    authentication_classes = (authentication.SessionAuthentication,)
    # permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "bitmall/step-2.html"

    def get(self, request):
        parent_uid = request.GET.get('parent_uid')
        openid, unionid = self.get_openid_and_unionid(request)
        if not self.valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)

        params = {
            'order_no': SaleTrade.gen_unikey(),
            'openid': openid,
            'unionid': unionid,
            'parent_uid': parent_uid,
        }

        # get activity product
        product = Product.objects
        params


        # generate pay info

        response = Response(params)
        # self.set_cookie_openid_and_unionid(response, openid, unionid)
        return response


    def post(self, request):
        # 验证码通过才可以进入本函数

        user = request.user
        bm_vip = XiaoluMama

        return redirect('/')