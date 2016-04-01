# coding:utf-8


import json
from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.core.urlresolvers import reverse

from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers 
from rest_framework.response import Response

from core.weixin.mixins import WeixinAuthMixin
from flashsale.pay.models_user import Customer
from shopback.items.models import Product


import logging
logger = logging.getLogger('django.reqeust')

class ActivityView(WeixinAuthMixin, APIView):
    
    authentication_classes = (authentication.SessionAuthentication, )
    permission_classes = ()
    renderer_classes = (renderers.TemplateHTMLRenderer,renderers.JSONRenderer)
    template_name = "promotion/discount_activity.html"
        
    def get_product_list(self):
        products = []
        if settings.DEBUG:
            pids = (1,2,3,4,5)
        else:
            pids = (36451,36443,36249,36449,36457)
        for pid in pids:
            product = Product.objects.get(id=pid)
            products.append(product)
        return products
        
    def get(self, request, *args, **kwargs):
        
        product_list = self.get_product_list()
        return Response({'product_list':product_list})