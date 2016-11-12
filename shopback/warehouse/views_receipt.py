# coding=utf-8
import datetime
import django_filters
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework import filters
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import APIException
from statistics.models import SaleStats
from shopback.warehouse import serializers, constants
from shopback.warehouse.models import ReceiptGoods


class ReceiptGoodsViewSet(viewsets.ModelViewSet):
    queryset = ReceiptGoods.objects.all().order_by('-created')
    serializer_class = serializers.ReceiptGoodsSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('=express_no',)

    def create(self, request, *args, **kwargs):
        content = request.POST
        express_no = content.get("express_no") or None
        express_company = content.get("express_company") or None
        weight = content.get("weight") or None
        receipt_type = content.get('receipt_type') or None

        receipt = self.queryset.filter(express_no=express_no, express_company=express_company).first()
        if not receipt:  # 不存在则创建
            receipt = ReceiptGoods(
                receipt_type=receipt_type,
                express_no=express_no,
                express_company=express_company,
                weight=weight,
                weight_time=datetime.datetime.now(),
                creator=request.user.username
            )
            receipt.save()
            serializer = self.get_serializer(receipt)
            return Response({"code": 0, "info": "添加成功", "receipt": serializer.data})
        return Response({"code": 1, "info": "已经添加过了", "receipt": ""})
