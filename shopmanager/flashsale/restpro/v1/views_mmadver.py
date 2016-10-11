# coding=utf-8
import datetime
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import exceptions
from rest_framework import filters
from rest_framework import viewsets, permissions, authentication, renderers
from rest_framework.response import Response

from flashsale.pay.models import Customer
from flashsale.xiaolumm.models import XiaoluMama, MamaTabVisitStats
from flashsale.xiaolumm.models.models_advertis import XlmmAdvertis, NinePicAdver, MamaVebViewConf
from . import serializers
from django_statsd.clients import statsd
from flashsale.xiaolumm.tasks_mama_fortune import task_mama_daily_tab_visit_stats


class XlmmAdvertisViewSet(viewsets.ModelViewSet):
    """
    ### 特卖平台－代理公告API:
    - {prefix}[.format] method:get : 获取登陆用户的代理公告
    """
    queryset = XlmmAdvertis.objects.all()
    serializer_class = serializers.XlmmAdvertisSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = get_object_or_404(XiaoluMama, openid=customer.unionid)
        return self.queryset.filter(show_people=xlmm.agencylevel, is_valid=True)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        advers = []
        now = datetime.datetime.now()
        for adver in queryset:
            if now >= adver.start_time and now <= adver.end_time:
                advers.append(adver)
        serializer = self.get_serializer(advers, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        return Response({})


class NinePicAdverFilter(filters.FilterSet):
    class Meta:
        model = NinePicAdver
        fields = ['id', 'sale_category']


class NinePicAdverViewSet(viewsets.ModelViewSet):
    """
    ### 特卖平台－九张图API:
    - {prefix}[.format] method:get : 获取九张图
    `could_share`: 标记当前的九张图记录是否可以用来分享
    """
    queryset = NinePicAdver.objects.all()
    serializer_class = serializers.NinePicAdverSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = NinePicAdverFilter

    def get_today_queryset(self, queryset):
        yesetoday = datetime.date.today() - datetime.timedelta(days=1)
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        now = datetime.datetime.now()
        queryset = queryset.filter(start_time__gte=yesetoday,
                                   start_time__lt=tomorrow).filter(start_time__lt=now)
        return queryset

    def list(self, request, *args, **kwargs):
        customer = Customer.objects.get(user=request.user)
        xlmm = customer.get_charged_mama()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.get_today_queryset(queryset).order_by('-start_time')
        request.data._mutable = True
        request.data.update({"mama_id": xlmm.id})
        request.data._mutable = False
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        # 统计代码
        statsd.incr('xiaolumm.ninepic_count')
        task_mama_daily_tab_visit_stats.delay(xlmm.id, MamaTabVisitStats.TAB_DAILY_NINEPIC)
        return Response(serializer.data)

    @transaction.atomic()
    def update(self, request, *args, **kwargs):
        """
        功能: 用户更新分享次数和保存次数
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        save_times = request.data.get('save_times') or 0
        share_times = request.data.get('share_times') or 0
        save_times = min(int(save_times), 1)
        share_times = min(int(share_times), 1)
        request.data._mutable = True
        request.data.update({'save_times': instance.save_times + save_times})
        request.data.update({'share_times': instance.share_times + share_times})
        request.data._mutable = False
        serializer = serializers.ModifyTimesNinePicAdverSerialize(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException("方法不允许")


class MamaVebViewConfFilter(filters.FilterSet):
    class Meta:
        model = MamaVebViewConf
        fields = ['version', "id"]


class MamaVebViewConfViewSet(viewsets.ModelViewSet):
    """
    ### 小鹿妈妈主页webview配置接口:
    - [/rest/v1/mmwebviewconfig](/rest/v1/mmwebviewconfig) 配置列表(仅返回有效配置):
        * method : GET
            * 可过滤字段：　`version`, `id`
    """
    queryset = MamaVebViewConf.objects.filter(is_valid=True)
    serializer_class = serializers.MamaVebViewConfSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = MamaVebViewConfFilter

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED!')
