# coding=utf-8

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer
from rest_framework.views import APIView
from rest_framework import filters

from shopback.items.models import Product, ProductSku
from flashsale.pay.models import SaleTrade, SaleOrder
from flashsale.pay import serializers


class SaleTradeManageAPIView(generics.ListCreateAPIView):

    queryset = SaleTrade.objects.all()
    serializer_class = serializers.ProductSerializer
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):

        sku_idstr = request.GET.get('aggsku_str')
        skuid_map_list = [tp.split('|') for tp in sku_idstr.split(',') if tp.strip()]

        SaleOrder.objects.filter()


    def post(self, request, *args, **kwargs):
        pass

