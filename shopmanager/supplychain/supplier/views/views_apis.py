# -*- coding:utf8 -*-
import time
import datetime
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db import transaction

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions

from supplychain.supplier.models import (
    SaleSupplier,
    SaleProduct,
    SaleCategory,
    SupplierZone,
    SaleProductManage,
    SaleProductManageDetail
)
from supplychain.supplier import serializers

import logging
logger = logging.getLogger(__name__)

class SaleSupplierViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ###供应商REST API接口：
    - 列表过滤条件: category, supplier_name, supplier_type, supplier_zone
    - /list_filters: 获取供应商过滤条件
    """
    queryset = SaleSupplier.objects.all()
    serializer_class = serializers.SaleSupplierSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_fields = ('category', 'supplier_name', 'supplier_type', 'supplier_zone')

    @list_route(methods=['get'])
    def list_filters(self, request, *args, **kwargs):
        categorys = SaleCategory.objects.filter(status=SaleCategory.NORMAL)
        return Response({
            'categorys': categorys.values_list('id','name','parent_cid','is_parent','sort_order'),
            'supplier_type': SaleSupplier.SUPPLIER_TYPE,
            'supplier_zone': SupplierZone.objects.values_list('id','name')
        })


class SaleProductViewSet(viewsets.ModelViewSet):
    """
    ###排期管理商品REST API接口：
    - 列表过滤条件: sale_supplier, sale_category
    """
    queryset = SaleProduct.objects.all()
    serializer_class = serializers.SimpleSaleProductSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_fields = ('sale_supplier', 'sale_category')

    def destroy(self, request, *args, **kwargs):
        raise NotImplemented


class SaleScheduleViewSet(viewsets.ModelViewSet):
    """
    ###排期管理REST API接口：
    - 列表过滤条件: schedule_type, sale_suppliers
    - /aggregate: 获取按日期聚合排期列表
    """
    queryset = SaleProductManage.objects.all()
    serializer_class = serializers.SimpleSaleProductManageSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_fields = ('schedule_type', 'sale_suppliers')

    @list_route(methods=['get'])
    def aggregate(self, request, *args, **kwargs):
        sale_date  = request.GET.get('sale_date','')
        if not sale_date:
            start_date = datetime.date.today() - datetime.timedelta(days=7)
            queryset = self.queryset.filter(sale_time__gte=start_date)
        else:
            sale_date = datetime.datetime.strftime(sale_date, '%Y-%m-%d').date()
            queryset = self.queryset.filter(sale_time=sale_date)

        schedule_values = queryset.values(
            'sale_time', 'id', 'schedule_type', 'product_num', 'lock_status')
        aggregate_data = {}
        for value in schedule_values:
            sdate = value['sale_time'].strftime("%Y-%m-%d")
            product_num = value['product_num']
            if sdate in aggregate_data:
                aggregate_data[sdate]['schedules'].append(value)
                aggregate_data[sdate]['product_sum'] += product_num
            else:
                aggregate_data[sdate] = {
                    'schedule_list': [value],
                    'schedule_date': sdate,
                    'product_sum': product_num
                }
        aggregate_list = sorted(aggregate_data.values(), key=lambda x:x['schedule_date'],reverse=True)
        return Response(aggregate_list)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = serializers.SaleProductManageSerializer(instance)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        raise NotImplemented


class SaleScheduleDetailViewSet(viewsets.ModelViewSet):
    """
    ###排期管理商品REST API接口：
    -
    """
    queryset = SaleProductManageDetail.objects.all()
    serializer_class = serializers.SaleProductManageDetailSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def list(self, request, schedule_id=None, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if schedule_id:
            queryset = queryset.filter(schedule_manage_id=schedule_id)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        raise NotImplemented




