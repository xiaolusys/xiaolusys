# coding=utf-8
""" 产品退货记录分析　"""
from rest_framework import viewsets
from . import serializers
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response
from shopback.refunds.models_refund_rate import ProRefunRcord
from rest_framework.decorators import list_route
import datetime


class ProRefRcdViewSet(viewsets.ModelViewSet):
    queryset = ProRefunRcord.objects.all()
    serializer_class = serializers.ProRefunRcordSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        queryset = self.queryset.filter(contactor=request.user.id)
        return queryset

    def super_admin_query(self, request):
        if request.user.has_perm('refunds.browser_all_pro_duct_ref_lis'):
            queryset = self.queryset
        else:
            queryset = self.filter_queryset(self.get_owner_queryset(request))
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.super_admin_query(request)
        queryset = queryset.order_by('product')[::-1]  # 产品id排序
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return


class CalcuProRefRcd(viewsets.ModelViewSet):
    queryset = ProRefunRcord.objects.all()
    serializer_class = serializers.ProRefunRcdSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        queryset = self.queryset.filter(contactor=request.user.id)
        return queryset

    def super_admin_query(self, request):
        if request.user.has_perm('refunds.browser_all_pro_duct_ref_lis'):
            queryset = self.queryset
        else:
            queryset = self.filter_queryset(self.get_owner_queryset(request))
        return queryset

    def time_zone_query(self, request, queryset):
        content = request.REQUEST
        today = datetime.date.today()
        fifth_day = today - datetime.timedelta(days=15)
        time_from = content.get("date_from", fifth_day)
        time_to = content.get("date_to", today)
        if isinstance(time_from, str) and isinstance(time_to, str):
            year, mont, day = map(int, time_from.split('-'))
            time_from = datetime.date(year, mont, day)
            year, mont, day = map(int, time_from.split('-'))
            time_to = datetime.date(year, mont, day)
        query = queryset.filter(sale_date__range=(time_from, time_to))
        return query

    @list_route(methods=['get'])
    def time_zone(self, request, *args, **kwargs):
        """ 过滤时间段(创建时间：上架时间之后产生了该model记录后的时间)的产品退货记录　"""
        queryset = self.super_admin_query(request)
        tzone_query = self.time_zone_query(request, queryset)
        serializer = self.get_serializer(tzone_query, many=True)
        return Response(serializer.data)
