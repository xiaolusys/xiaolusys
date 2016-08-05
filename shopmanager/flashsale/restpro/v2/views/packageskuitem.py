# coding=utf-8
import os, urlparse
import datetime

from django.conf import settings
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework.views import APIView

from flashsale.pay.models import Customer
from flashsale.restpro import permissions as perms
from ..serializers import packageskuitem_serializers

import logging
logger = logging.getLogger(__name__)


from shopback.trades.models import PackageSkuItem


def get_customer_id(user):
    customer = Customer.objects.normal_customer.filter(user=user).first()
    customer_id = None
    if customer:
        customer_id = customer.id
    #customer_id = 19 # debug test
    return customer_id


class PackageSkuItemView(APIView):
    """
    Return package sku items upon query with sale_trade_id or receiver_mobile.
    # NOTICE:this api is move to views_trade_v2
    """

    queryset = PackageSkuItem.objects.all()
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_queryset(self, request):
        content = request.GET

        sale_trade_id = content.get("sale_trade_id")
        if sale_trade_id:
            return self.queryset.filter(sale_trade_id=sale_trade_id)

        receiver_mobile = content.get("receiver_mobile")
        if receiver_mobile:
            return self.queryset.filter(receiver_mobile=receiver_mobile)

        return []

    
    def get(self, request, *args, **kwargs):
        query_set = self.get_queryset(request)
        serializer = packageskuitem_serializers.PackageSkuItemSerializer(query_set, many=True)
        data = sorted(serializer.data, key=lambda x: x['package_group_key'])
        return Response(data)

        


