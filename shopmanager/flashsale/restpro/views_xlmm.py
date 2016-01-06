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


class XiaoluMamaViewSet(viewsets.ModelViewSet):
    """
    ### 特卖平台－小鹿妈妈代理API:
    - {prefix}[.format] method:get : 获取登陆用户的代理基本信息
    - {prefix}/list_base_data　method:get : 获取代理推荐人信息
    - {prefix}/agency_info　method:get : 代理整理数据  
    `recommend_num`: 总推荐数量  
    `clk_num`: 今日点击  
    `shop_num`: 今日订单  
    `mobile`: 手机号
    `all_shop_num`: 所有订单数 
    `mco`: 确定支出  
    `ymco`: 昨日确定支出  
    `pdc`: 总待确定金额  
    `ymci`:昨日确定收入  
    `mci`: 确定收入  
    `cash`: 账户现金  
    `mama_link`: 专属链接
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
    def agency_info(self, request):
        """ wap 版本页面数据整理显示　"""
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm

        recommend_num = self.queryset.filter(referal_from=xlmm.mobile).count()  # 总推荐数量
        cash = xlmm.cash_money  # 账户现金
        carry_logs = CarryLog.objects.filter(xlmm=xlmm.id).exclude(status=CarryLog.CANCELED)  # 该代理的收支记录
        today = datetime.date.today()
        yestoday = today - datetime.timedelta(days=1)
        cfm_in = carry_logs.filter(carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED)
        cfm_out = carry_logs.filter(carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED)
        yst_cfm_in = carry_logs.filter(carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED, carry_date=yestoday)
        yst_cfm_out = carry_logs.filter(carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED, carry_date=yestoday)
        pending = carry_logs.filter(status=CarryLog.PENDING)
        nmc_in = carry_logs.filter(carry_type=CarryLog.CARRY_IN, status__in=(CarryLog.CONFIRMED, CarryLog.PENDING),
                                   carry_date=today)

        mci = (cfm_in.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0  # 确定收入
        mco = (cfm_out.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0  # 确定支出
        ymci = (yst_cfm_in.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0  # 昨日确定收入
        ymco = (yst_cfm_out.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0  # 昨日确定支出
        pdc = (pending.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0  # 总待确定金额
        nmci = (nmc_in.aggregate(total_value=Sum('value')).get('total_value') or 0) / 100.0  # 今日收入(含待收入)
        mmclog = {"mci": mci, "mco": mco, "ymci": ymci, "ymco": ymco, "pdc": pdc, "nmci": nmci}

        # 今日有效点击数量
        clks = ClickCount.objects.filter(linkid=xlmm.id, date=today)
        clk_num = clks.aggregate(clk_num=Sum('valid_num')).get('clk_num') or 0
        # 今日订单
        t_from = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        t_to = datetime.datetime(today.year, today.month, today.day, 23, 59, 59)
        all_shops = StatisticsShopping.objects.filter(linkid=xlmm.id, status=StatisticsShopping.FINISHED)
        all_shop_num = all_shops.count()
        shop_num = all_shops.filter(shoptime__gte=t_from, shoptime__lte=t_to).count()  # 今日订单数量
        mama_link = "http://xiaolu.so/m/{0}/".format(xlmm.id)  # 专属链接
        data = {"xlmm": xlmm.id, "mobile": xlmm.mobile, "recommend_num": recommend_num, "cash": cash, "mmclog": mmclog,
                "clk_num": clk_num, "mama_link": mama_link, "shop_num": shop_num, "all_shop_num": all_shop_num}
        return Response(data)


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
        yestoday = datetime.date.today() - datetime.timedelta(days=1)
        qst_confirm_in = queryset.filter(carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED)
        qst_confirm_out = queryset.filter(carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED)
        qst_yst_confirm_in = queryset.filter(carry_type=CarryLog.CARRY_IN, status=CarryLog.CONFIRMED,
                                             carry_date=yestoday)
        qst_yst_confirm_out = queryset.filter(carry_type=CarryLog.CARRY_OUT, status=CarryLog.CONFIRMED,
                                              carry_date=yestoday)
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
        today = datetime.date.today()
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        tqs = queryset.filter(date=today)  # 今天的统计记录
        serializer = self.get_serializer(tqs, many=True)
        return Response(serializer.data)


class StatisticsShoppingViewSet(viewsets.ModelViewSet):
    """
    ## 特卖平台－小鹿妈妈购买统计API:
    - {prefix}[.format]: 获取登陆用户的购买统计记录
    - {prefix}/today_shops　method:get : 当天的购买统计记录
    - {prefix}/days_num?days=[days] method: get : 过去days天每天的推广交易数量
    - {prefix}/noedaynum_by_days?days=[days] method: get :获取days天前当天的订单数量,没有参数则返回days=0的对应数据
        `shops_num:` 订单数量
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

    def get_tzone_queryset(self, days, request):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        today = datetime.datetime.today()
        tf = datetime.datetime(today.year, today.month, today.day, 0, 0, 0) - datetime.timedelta(days=days)
        tt = datetime.datetime.now()
        tqs = queryset.filter(shoptime__gte=tf, shoptime__lte=tt)
        return tqs

    @list_route(methods=['get'])
    def today_shops(self, request):
        tqs = self.get_tzone_queryset(days=1, request=request)
        serializer = self.get_serializer(tqs, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def days_num(self, request):
        """ 根据给的天数，返回天数内每天的专属订单的数量　"""
        days = int(request.REQUEST.get('days', 0))
        data = [(self.get_tzone_queryset(days=i, request=request).filter(status__in=(
            StatisticsShopping.FINISHED,
            StatisticsShopping.WAIT_SEND)).count())
                for i in range(0, days)]
        data_cp = data
        d = [data[i] - data_cp[i - 1] for i in range(days)[::-1] if i > 0]
        d.append(data[0])
        return Response(d[::-1])

    @list_route(methods=['get'])
    def noedaynum_by_days(self, request):
        """　根据日期参数传该日期的订单数量　"""
        content = request.REQUEST
        days = content.get("days", 0)
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        days = int(days)
        today = datetime.date.today()  # 今天日期
        target_date = today - datetime.timedelta(days=days)
        target_date_end = target_date + datetime.timedelta(days=1)
        num = queryset.filter(shoptime__gte=target_date, shoptime__lte=target_date_end,
                              status__in=(StatisticsShopping.FINISHED, StatisticsShopping.WAIT_SEND)).count()
        return Response({"shops_num": num})


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
    cashout_type = {"c1": 80, "c2": 200}

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
        cash_type = request.REQUEST.get('ctype', None)
        if cash_type is None:  # 参数错误
            return Response({"code": 1})
        value = self.cashout_type.get(cash_type)
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)  # 找到xlmm
        could_cashout = xlmm.get_cash_iters()  # 可以提现的金额
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        if queryset.filter(status=CashOut.PENDING).count() > 0:  # 如果有待审核提现记录则不予再次创建记录
            return Response({"code": 3})
        if could_cashout < value:  # 如果可以提现金额不足
            return Response({"code": 2})
        # 满足提现请求　创建提现记录
        CashOut.objects.create(xlmm=xlmm.id, value=value)
        return Response({"code": 0})

