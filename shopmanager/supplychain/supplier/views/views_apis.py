# -*- coding:utf8 -*-
import time
import json
import datetime
import django_filters
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db import transaction

from rest_framework import viewsets
from rest_framework.parsers import JSONParser
from rest_framework.decorators import detail_route, list_route
from rest_framework.decorators import parser_classes
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions
from rest_framework import filters
from django_filters import Filter
from django_filters.fields import Lookup

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


class ListFilter(Filter):
    def filter(self, qs, value):
        value_list = value.split(u',')
        return super(ListFilter, self).filter(qs, Lookup(value_list, 'in'))


class SaleSupplierFilter(filters.FilterSet):
    id = ListFilter(name='id')
    category = ListFilter(name='category')
    supplier_zone = ListFilter(name='supplier_zone')

    class Meta:
        model = SaleSupplier
        fields = ['id', 'category', 'supplier_name', 'supplier_type', 'supplier_zone']


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
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    ordering_fields = ('id', 'total_refund_num', 'total_sale_num', 'created', 'modified')
    filter_class = SaleSupplierFilter

    @list_route(methods=['get'])
    def list_filters(self, request, *args, **kwargs):
        categorys = SaleCategory.objects.filter(status=SaleCategory.NORMAL)
        return Response({
            'categorys': categorys.values_list('id','name','parent_cid','is_parent','sort_order'),
            'supplier_type': SaleSupplier.SUPPLIER_TYPE,
            'supplier_zone': SupplierZone.objects.values_list('id','name')
        })

    def list(self, request, *args, **kwargs):
        ordering = request.REQUEST.get('ordering')
        queryset = self.filter_queryset(self.get_queryset())
        if ordering == 'refund_rate':
            queryset = queryset.extra(select={'refund_rate': 'total_refund_num/total_sale_num'}).order_by(
                'refund_rate')
        if ordering == '-refund_rate':
            queryset = queryset.extra(select={'refund_rate': 'total_refund_num/total_sale_num'}).order_by(
                '-refund_rate')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SaleProductFilter(filters.FilterSet):
    id = ListFilter(name='id')
    sale_supplier = ListFilter(name='sale_supplier')

    class Meta:
        model = SaleProduct
        fields = ['id', 'sale_supplier', 'sale_category', 'sale_supplier__supplier_name', 'status']


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
    # filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = SaleProductFilter

    def destroy(self, request, *args, **kwargs):
        raise NotImplemented


class SaleProductManageFilter(filters.FilterSet):
    sale_time_start = django_filters.DateFilter(name="sale_time", lookup_type='gte')
    sale_time_end = django_filters.DateFilter(name="sale_time", lookup_type='lte')

    class Meta:
        model = SaleProductManage
        fields = ['sale_time_start', 'sale_time_end', 'schedule_type', 'sale_suppliers']


class SaleScheduleViewSet(viewsets.ModelViewSet):
    """
    ###排期管理REST API接口：
    - schedule_type: (brand, 品牌),(atop, TOP榜),(topic, 专题),(sale, 特卖)
    - 列表过滤条件: schedule_type, sale_suppliers
    - /aggregate: 获取按日期聚合排期列表
    """
    queryset = SaleProductManage.objects.all()
    serializer_class = serializers.SimpleSaleProductManageSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = SaleProductManageFilter
    # filter_fields = ('schedule_type', 'sale_suppliers')
    ordering_fields = ('sale_time', 'id', 'created', 'modified', 'product_num')

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

    def create(self, request, *args, **kwargs):
        user = request.user
        request.data.update({"responsible_person_name": user.username, "responsible_people_id": user.id})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.SaleProductManageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SaleScheduleDetailViewSet(viewsets.ModelViewSet):
    """
    ###排期管理商品REST API接口：
    -
    """
    queryset = SaleProductManageDetail.objects.all()
    serializer_class = serializers.SaleProductManageDetailSerializer
    # authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # permission_classes = (permissions.IsAuthenticated,)
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

    @parser_classes(JSONParser)
    def create_manage_detail(self, request, schedule_id, *args, **kwargs):
        sale_product_id = request.data.get('sale_product_id') or None
        sale_product = get_object_or_404(SaleProduct, id=sale_product_id)
        detail = SaleProductManageDetail.objects.filter(schedule_manage=schedule_id,
                                                        sale_product_id=sale_product.id).first()
        if detail:
            serializer = serializers.SaleProductManageDetailSimpleSerializer(detail)
            return Response(serializer.data, status=status.HTTP_302_FOUND)
        request.data.update({
            "schedule_manage": schedule_id,
            "sale_product_id": sale_product_id,
            "name": sale_product.title,
            "today_use_status": SaleProductManageDetail.NORMAL,
            "pic_path": sale_product.pic_url,
            "product_link": sale_product.product_link,
            "sale_category": sale_product.sale_category.full_name
        })
        serializer = serializers.SaleProductManageDetailSimpleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def modify_manage_detail(self, request, schedule_id, pk, *args, **kwargs):
        kwargs['partial'] = True
        partial = kwargs.pop('partial', False)
        instance = get_object_or_404(SaleProductManageDetail, id=pk)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
