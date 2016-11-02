# coding=utf-8
import datetime
import django_filters
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from statistics import serializers
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route, api_view
from rest_framework.exceptions import APIException
from statistics.models import SaleStats
from statistics import constants
from rest_framework import filters
from django_filters import Filter
from django_filters.fields import Lookup
from shopback.categorys.models import ProductCategory


class ListFilter(Filter):
    def filter(self, qs, value):
        value_list = value.split(u',')
        return super(ListFilter, self).filter(qs, Lookup(value_list, 'in'))


class SaleStatsFilter(filters.FilterSet):
    id = ListFilter(name='id')
    date_field_start = django_filters.DateFilter(name="date_field", lookup_type='gte')
    date_field_end = django_filters.DateFilter(name="date_field", lookup_type='lte')

    class Meta:
        model = SaleStats
        fields = ['id', 'current_id', 'date_field', 'num',
                  'timely_type', 'record_type', 'status',
                  'date_field_start', 'date_field_end']


class SaleStatsViewSet(viewsets.ModelViewSet):
    queryset = SaleStats.objects.all()
    serializer_class = serializers.StatsSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    ordering_fields = ('id', 'num', 'payment', 'date_field')
    filter_class = SaleStatsFilter

    def create(self, request, *args, **kwargs):
        raise APIException('method not allowed!')

    def update(self, request, *args, **kwargs):
        raise APIException('method not allowed!')

    def partial_update(self, request, *args, **kwargs):
        raise APIException('method not allowed!')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def list_aggregate(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # 聚合同一个类型　同一个current_id 一段时间　各种状态的　到同一个记录当中
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductCategoryAPI(viewsets.ViewSet):
    queryset = ProductCategory.objects.all()
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        cid = request.GET.get('cid')
        if cid:
            categories = ProductCategory.objects.filter(parent_cid=cid)
        else:
            categories = ProductCategory.objects.filter(is_parent=True)
        json = []
        for item in categories:
            json.append({
                'cid': item.cid,
                'name': item.name,
            })
        return Response(json)
