# coding=utf-8
__author__ = 'yan.huang'
from rest_framework import generics, viewsets, permissions, authentication, renderers
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework import exceptions
from flashsale.promotion.serializers import StockSaleSerializers
from flashsale.promotion.models.stocksale import *
import logging

log = logging.getLogger('django.request')


class StockSaleViewSet(viewsets.GenericViewSet):
    """
        库存
    """
    queryset = StockSale.objects.all()
    serializer_class = StockSaleSerializers
    authentication_classes = (authentication.SessionAuthentication, permissions.DjangoModelPermissions, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @list_route(methods=['GET', 'POST'])
    def gen_new_stock_sale(self, request):
        StockSale.gen_new_stock_sale()
        return Response()

    @list_route(methods=['GET', 'POST'])
    def gen_new_activity(self, request):
        StockSale.gen_new_activity()
        return Response()