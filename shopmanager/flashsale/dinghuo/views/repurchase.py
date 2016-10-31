# coding:utf-8
"""
    补单进货
"""
import re
from django.db.models import *
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, renderers, viewsets
from flashsale.dinghuo.models import OrderList
from rest_framework.response import Response


class RePurchaseViewSet(viewsets.GenericViewSet):
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer, renderers.BrowsableAPIRenderer)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = OrderList.objects.filter(created_by=OrderList.CREATED_BY_REPURCHASE)

    def create(self, request, pk=None):
        result = {}
        ol = get_object_or_404(OrderList, pk=pk)
        sku_ids = request.GET.get('sku_ids', '')
        product_ids = request.GET.get('product_ids', '')

        return Response(result, template_name='dinghuo/purchase/purchase.html')

    def create(self, request, pk=None):
        result = {}
        return Response(result, template_name='dinghuo/inbound.html')