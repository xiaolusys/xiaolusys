# coding=utf-8
from flashsale.xiaolumm.models import XiaoluMama, CarryLog, CashOut
from flashsale.clickcount.models import ClickCount
from flashsale.clickrebeta.models import StatisticsShopping
import datetime
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from flashsale.pay.models import Customer
from . import permissions as perms
from . import serializers
from django.forms import model_to_dict
from django.db.models import Sum


today = datetime.datetime.today()
yestoday = today - datetime.timedelta(days=1)

today_time_from = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
today_time_to = datetime.datetime(today.year, today.month, today.day, 23, 59, 59)
yestoday_time_from = datetime.datetime(yestoday.year, yestoday.month, yestoday.day, 0, 0, 0)
yestoday_time_to = datetime.datetime(yestoday.year, yestoday.month, yestoday.day, 23, 59, 59)


class XiaoluMamaViewSet(viewsets.ModelViewSet):
    """
    ### 特卖平台－小鹿妈妈代理API:
    - {prefix}[.format] method:get : 获取登陆用户的代理基本信息
    - {prefix}/list_base_data　method:get : 获取代理推荐人信息
    """
    queryset = XiaoluMama.objects.all()
    serializer_class = serializers.XiaoluMamaSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(openid=customer.unionid)  # 通过customer的unionid找 xlmm

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response()

    @list_route(methods=['get'])
    def list_base_data(self, request):
        """
        该代理推荐的人
        """
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        qst = self.queryset.filter(referal_from=xlmm.mobile)
        serializer = self.get_serializer(qst, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def agency_info(self):
        return Response()


class CarryLogViewSet(viewsets.ModelViewSet):
    """
    ## 特卖平台－小鹿妈妈收支记录API:
    - {prefix}[.format] : 获取登陆用户的收支记录信息
    - {prefix}/list_base_data　method:get : 账户基本信息页面显示
        - return :
        `mci`: 已经确认收入
        `mco`:　已经确认支出  　
        `ymci`:　昨天确认收入
        `ymco`: 昨天确认支出
        `pdc`: 待确认金额
    """
    queryset = CarryLog.objects.all()
    serializer_class = serializers.CarryLogSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        return self.queryset.filter(xlmm=xlmm.id)  # 对应的carrylog记录

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response()

    @list_route(methods=['get'])
    def list_base_data(self, request):
        """  账户基本信息页面显示　"""
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        qst_confirm_in = queryset.filter(carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED)
        qst_confirm_out = queryset.filter(carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED)
        qst_yst_confirm_in = queryset.filter(carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED,
                                             created__gte=yestoday_time_from, created__lte=yestoday_time_to)
        qst_yst_confirm_out = queryset.filter(carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED,
                                              created__gte=yestoday_time_from, created__lte=yestoday_time_to)
        qst_pending = queryset.filter(status=CarryLog.PENDING)

        mci = (qst_confirm_in.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0
        mco = (qst_confirm_out.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0
        ymci = (qst_yst_confirm_in.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0
        ymco = (qst_yst_confirm_out.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0
        pdc = (qst_pending.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0
        data = {"mci": mci, "mco": mco, "ymci": ymci, "ymco": ymco, "pdc": pdc}
        return Response(data)


class ClickCountViewSet(viewsets.ModelViewSet):
    """
    ## 特卖平台－小鹿妈妈点击API:
    - {prefix}[.format]: 获取登陆用户的点击记录
    - {prefix}/list_base_data　method:get : 当天的点击统计记录
    """
    queryset = ClickCount.objects.all()
    serializer_class = serializers.ClickCountSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        return self.queryset.filter(linkid=xlmm.id)  # 对应的xlmm的点击统计

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response()

    @list_route(methods=['get'])
    def list_base_data(self, request):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        tqs = queryset.filter(date=today.date())  # 今天的统计记录
        serializer = self.get_serializer(tqs, many=True)
        return Response(serializer.data)


class StatisticsShoppingViewSet(viewsets.ModelViewSet):
    """
    ## 特卖平台－小鹿妈妈购买统计API:
    - {prefix}[.format]: 获取登陆用户的购买统计记录
    - {prefix}/list_base_data　method:get : 当天的购买统计记录
    """
    queryset = StatisticsShopping.objects.all()
    serializer_class = serializers.StatisticsShoppingSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        return self.queryset.filter(linkid=xlmm.id)  # 对应的xlmm的购买统计

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response()

    @list_route(methods=['get'])
    def list_base_data(self, request):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        tqs = queryset.filter(shoptime__gte=today_time_from, shoptime__lte=today_time_to)  # 今天的统计记录
        serializer = self.get_serializer(tqs, many=True)
        return Response(serializer.data)


class CashOutViewSet(viewsets.ModelViewSet):
    """
    ## 特卖平台－小鹿妈妈购体现记录API:
    - {prefix}[.format]: 获取登陆用户的提现记录
    """
    queryset = CashOut.objects.all()
    serializer_class = serializers.CashOutSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        return self.queryset.filter(xlmm=xlmm.id)  # 对应的xlmm的购买统计

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """代理提现"""
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        # 创建体现记录
        return Response()