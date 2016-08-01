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
from core.options import get_systemoa_user, log_action
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION

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
    progress = ListFilter(name='progress')
    category = ListFilter(name='category')
    supplier_zone = ListFilter(name='supplier_zone')
    created_start = django_filters.DateFilter(name="created", lookup_type='gte')
    created_end = django_filters.DateFilter(name="created", lookup_type='lte')
    supplier_name = django_filters.CharFilter(name="supplier_name", lookup_type='contains')

    class Meta:
        model = SaleSupplier
        fields = ['id', 'category', 'supplier_name', 'supplier_type', 'supplier_zone', 'progress',
                  'created_start', 'created_end']


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
    ordering_fields = ('id', 'total_refund_num', 'total_sale_num', 'created', 'modified',
                       'figures__payment',
                       'figures__return_good_rate',
                       'figures__out_stock_num')
    filter_class = SaleSupplierFilter

    @list_route(methods=['get'])
    def list_filters(self, request, *args, **kwargs):
        categorys = SaleCategory.objects.filter(status=SaleCategory.NORMAL)
        return Response({
            'categorys': categorys.values_list('id', 'name', 'parent_cid', 'is_parent', 'sort_order'),
            'supplier_type': SaleSupplier.SUPPLIER_TYPE,
            'progress': SaleSupplier.PROGRESS_CHOICES,
            'supplier_zone': SupplierZone.objects.values_list('id', 'name')
        })

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.exclude(progress=SaleSupplier.REJECTED)
        ordering = request.REQUEST.get('ordering')
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
    status = ListFilter(name='status')
    sale_supplier = ListFilter(name='sale_supplier')
    min_price = django_filters.NumberFilter(name="price", lookup_type='gte')
    max_price = django_filters.NumberFilter(name="price", lookup_type='lte')

    class Meta:
        model = SaleProduct
        fields = ['id', 'sale_supplier', 'sale_category',
                  'sale_supplier__supplier_name', 'status',
                  'min_price', 'max_price']


class SaleProductViewSet(viewsets.ModelViewSet):
    """
    ### 排期管理商品REST API接口：
    - {prefix}: 选品
    - {prefix}/list_filters: 列表过滤条件
    method: get
    return: {'status':[...], 'categorys':[...]}
    """
    queryset = SaleProduct.objects.all()
    serializer_class = serializers.SimpleSaleProductSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    ordering_fields = ('created', 'modified', 'sale_time', 'remain_num', 'hot_value')
    filter_class = SaleProductFilter

    @list_route(methods=['get'])
    def list_filters(self, request, *args, **kwargs):
        categorys = SaleCategory.objects.filter(status=SaleCategory.NORMAL)
        return Response({
            'status': SaleProduct.STATUS_CHOICES,
            'categorys': categorys.values_list('id', 'name', 'parent_cid', 'is_parent', 'sort_order'),
        })

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.exclude(status=SaleProduct.REJECTED)  # 排除淘汰的产品
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
    permission_classes = (permissions.IsAuthenticated,
                          permissions.IsAdminUser,
                          permissions.DjangoModelPermissions)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = SaleProductManageFilter
    # filter_fields = ('schedule_type', 'sale_suppliers')
    ordering_fields = ('sale_time', 'id', 'created', 'modified', 'product_num')

    @list_route(methods=['get'])
    def aggregate(self, request, *args, **kwargs):
        sale_date = request.GET.get('sale_date', '')
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
        aggregate_list = sorted(aggregate_data.values(), key=lambda x: x['schedule_date'], reverse=True)
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

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        log_action(request.user, instance, CHANGE, u'修改字段:%s' % ''.join(request.data.keys()))
        self.perform_update(serializer)
        return Response(serializer.data)


class SaleScheduleDetailFilter(filters.FilterSet):
    order_weight = django_filters.NumberFilter(name="order_weight")

    class Meta:
        model = SaleProductManageDetail
        fields = ['order_weight', "id"]


class SaleScheduleDetailViewSet(viewsets.ModelViewSet):
    """
    ### 排期管理商品REST API接口：
    - /apis/chain/v1/saleschedule/<schedule_id>/product/<schedule_detail_id>:
      method: delete (授权用户可以删除)
    - /apis/chain/v1/saleschedule/<schedule_id>/adjust_order_weight/<schedule_detail_id>:
      method: patch
      args:
        移动方向: `direction`
         plus: 向上
         minus: 向下　
         移动距离: `distance`
    """
    queryset = SaleProductManageDetail.objects.all()
    serializer_class = serializers.SaleProductManageDetailSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions, permissions.IsAdminUser)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    ordering_fields = ('order_weight', 'is_promotion', 'sale_category')
    filter_class = SaleScheduleDetailFilter

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
        if request.user.has_perm('supplier.delete_schedule_detail'):
            instance = self.get_object()
            manager = instance.schedule_manage
            self.perform_destroy(instance)
            manager.save(update_fields=['product_num'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    @parser_classes(JSONParser)
    @transaction.atomic()
    def create_manage_detail(self, request, schedule_id, *args, **kwargs):
        sale_product_id = request.data.get('sale_product_id') or None
        sale_products = SaleProduct.objects.filter(id__in=sale_product_id)
        details = SaleProductManageDetail.objects.filter(schedule_manage_id=schedule_id,
                                                         today_use_status=SaleProductManageDetail.NORMAL)
        for sale_product in sale_products:
            order_weight = details.count() + 1
            request.data.update({
                "schedule_manage": schedule_id,
                "sale_product_id": sale_product.id,
                "name": sale_product.title,
                "today_use_status": SaleProductManageDetail.NORMAL,
                "pic_path": sale_product.pic_url,
                "product_link": sale_product.product_link,
                "sale_category": sale_product.sale_category.full_name,
                "order_weight": order_weight
            })
            serializer = serializers.SaleProductManageDetailSimpleSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        return Response(status=status.HTTP_201_CREATED)

    def modify_manage_detail(self, request, schedule_id, pk, *args, **kwargs):
        kwargs['partial'] = True
        partial = kwargs.pop('partial', False)
        instance = get_object_or_404(SaleProductManageDetail, id=pk)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        log_action(request.user, instance, CHANGE, u'修改字段:%s' % ''.join(request.data.keys()))
        self.perform_update(serializer)
        return Response(serializer.data)

    def adjust_order_weight(self, request, schedule_id, pk, *args, **kwargs):
        """
        调整排序字段
        当前id : instance id
        移动方向: plus  minus
        移动距离: distance
        """
        direction = request.data.get('direction') or None
        distance = request.data.get('distance') or None
        instance = get_object_or_404(SaleProductManageDetail, id=pk)
        if not (direction and distance):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(schedule_manage=instance.schedule_manage,
                                        today_use_status=SaleProductManageDetail.NORMAL).order_by('order_weight')
        if direction == 'plus':  # 变大
            heiger_details = queryset.filter(order_weight__gt=instance.order_weight)
            if heiger_details.count() <= 0:
                raise exceptions.APIException(u'已经最大了')
            # 当前order_weight 和　目标order_weight 之间的　instance 需要变化
            zone_details = heiger_details.filter(order_weight__lte=instance.order_weight + int(distance))
            abs_distance = zone_details.count()
            for detail in zone_details:
                detail.order_weight -= 1
                detail.save(update_fields=['order_weight'])
            instance.order_weight = instance.order_weight + abs_distance
            instance.save(update_fields=['order_weight'])

        elif direction == 'minus':  # 变小
            lower_details = queryset.filter(order_weight__lt=instance.order_weight)
            if lower_details.count() <= 0:
                raise exceptions.APIException(u'已经最小了')
            zone_details = lower_details.filter(order_weight__gte=instance.order_weight - int(distance))
            abs_distance = zone_details.count()
            for detail in zone_details:
                detail.order_weight += 1
                detail.save(update_fields=['order_weight'])
            instance.order_weight = instance.order_weight - abs_distance
            instance.save(update_fields=['order_weight'])
        return Response(status=status.HTTP_200_OK)
