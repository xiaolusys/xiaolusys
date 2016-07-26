# coding=utf-8
"""
代理或者用户给选品点赞，统计商品的热度ＡＰＩ
"""

from django.shortcuts import get_object_or_404
from django.forms import model_to_dict
from django.db.models import F

from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework import renderers
from rest_framework import status

import hashlib
import datetime

from flashsale.restpro import permissions as perms
from . import serializers

from supplychain.supplier.models import SaleProduct
from flashsale.pay.models import Customer
from supplychain.supplier.models import SalePraise, HotProduct
from common.modelutils import update_model_fields


class SaleProductViewSet(viewsets.ModelViewSet):
    """
    特卖选品接口:
    - {prefix}/ 获取特卖选品

    """
    queryset = SaleProduct.objects.all()
    serializer_class = serializers.SaleProductSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_wanter_queryset(self, request):
        """ 选择通过和取样状态的选品　上架时间在未来?天"""
        today = datetime.datetime.today()
        t_day = today - datetime.timedelta(days=150)
        time_to = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        time_from = datetime.datetime(t_day.year, t_day.month, t_day.day, 23, 59, 59)
        return self.queryset.filter(created__gte=time_from, created__lte=time_to, voting=True,
                                    status__in=(SaleProduct.PASSED, SaleProduct.PURCHASE))

    def get_own_today_queryset(self, cus_id):
        today = datetime.datetime.today()
        time_from = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        time_to = datetime.datetime(today.year, today.month, today.day, 23, 59, 59)
        queryset = SalePraise.objects.filter(created__gte=time_from, created__lte=time_to,
                                             pro_from=SalePraise.SALE_PRODUCT,
                                             cus_id=cus_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_wanter_queryset(request))
        queryset = queryset.order_by("created")[::-1]
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response()

    @detail_route(methods=['post'])
    def change_hot_val(self, request, pk=0):
        """ 增加选品热度值 """
        pk = int(pk)
        result = {}
        sale_pro = get_object_or_404(SaleProduct, id=pk)
        customer = get_object_or_404(Customer, user=request.user)
        # 查看今天点赞的个数超过10个就不允许点击
        today_queryset = self.get_own_today_queryset(customer.id)
        today_count = today_queryset.count()
        if today_count >= 10:
            result['hot_val'] = sale_pro.hot_value
            result['today_count'] = today_count
            return Response(result)

        # 创建点赞记录
        sale_praise, state = SalePraise.objects.get_or_create(sale_id=sale_pro.id, cus_id=customer.id)
        if state:  # 点赞 state 为True表示创建了
            sale_pro.hot_value = F('hot_value') + 1  # 热度加１
            update_model_fields(sale_pro, update_fields=['hot_value'])
            sale_praise.praise = True
            update_model_fields(sale_praise, update_fields=['praise'])  # 点赞

        sale_pro = get_object_or_404(SaleProduct, id=pk)
        result['hot_val'] = sale_pro.hot_value
        result['today_count'] = today_count
        return Response(result)


class HotProductViewSet(viewsets.ModelViewSet):
    """
    特卖爆款接口:
    - {prefix}/ 获取特卖爆款

    """
    queryset = HotProduct.objects.all()
    serializer_class = serializers.HotProductSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_wanter_queryset(self, request):
        """ 选择通过和取样状态的选品　上架时间在未来?天"""
        today = datetime.datetime.today()
        t_day = today - datetime.timedelta(days=15)
        time_from = datetime.datetime(t_day.year, t_day.month, t_day.day, 0, 0, 0)
        time_to = datetime.datetime(today.year, today.month, today.day, 23, 59, 59)
        return self.queryset.filter(created__gte=time_from, created__lte=time_to, voting=True,
                                    status__in=(HotProduct.SELECTED,))

    def get_own_today_queryset(self, cus_id):
        today = datetime.datetime.today()
        time_from = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        time_to = datetime.datetime(today.year, today.month, today.day, 23, 59, 59)
        queryset = SalePraise.objects.filter(created__gte=time_from, created__lte=time_to,
                                             pro_from=SalePraise.Hot_Product,
                                             cus_id=cus_id)
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_wanter_queryset(request))
        queryset = queryset.order_by("created")[::-1]
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response()

    @detail_route(methods=['post'])
    def change_hot_val(self, request, pk=0):
        """ 增加选品热度值 """
        pk = int(pk)
        result = {}
        hot_pro = get_object_or_404(HotProduct, id=pk)
        customer = get_object_or_404(Customer, user=request.user)
        # 查看今天点赞的个数超过10个就不允许点击
        today_queryset = self.get_own_today_queryset(customer.id)
        today_count = today_queryset.count()
        if today_count >= 1:
            result['hot_val'] = hot_pro.hot_value
            result['today_count'] = today_count
            return Response(result)

        # 创建点赞记录
        sale_praise, state = SalePraise.objects.get_or_create(sale_id=hot_pro.id, cus_id=customer.id,
                                                              pro_from=SalePraise.Hot_Product)
        if state:  # 点赞 state 为True表示创建了
            hot_pro.hot_value = F('hot_value') + 1  # 热度加１
            update_model_fields(hot_pro, update_fields=['hot_value'])
            sale_praise.praise = True
            update_model_fields(sale_praise, update_fields=['praise'])  # 点赞

        hot_pro = get_object_or_404(HotProduct, id=pk)
        result['hot_val'] = hot_pro.hot_value
        result['today_count'] = today_count
        return Response(result)
