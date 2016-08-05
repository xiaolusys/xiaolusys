# coding=utf-8
import datetime
import os
import random

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import exceptions
from rest_framework import filters
from rest_framework import viewsets, permissions, authentication, renderers
from rest_framework.response import Response

from flashsale.pay.models import Customer
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.xiaolumm.models.models_advertis import XlmmAdvertis, NinePicAdver, MamaVebViewConf
from . import serializers


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

    def get_today_queryset(self):
        yesetoday = datetime.date.today() - datetime.timedelta(days=1)
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        queryset = self.queryset.filter(start_time__gte=yesetoday, start_time__lt=tomorrow)
        return queryset

    def get_mama_link(self, request, model_id=None):
        """
        获取代理专属链接
        """
        customer = Customer.objects.get(user=request.user)
        xlmm = customer.get_charged_mama()
        if xlmm:
            if model_id:
                return os.path.join(settings.M_SITE_URL,
                                    "m/{0}/?next=mall/product/details/{1}".format(xlmm.id,
                                                                                  model_id))  # 专属链接
            return os.path.join(settings.M_SITE_URL,
                                "m/{0}/".format(xlmm.id))  # 专属链接
        else:
            return ''

    def list(self, request, *args, **kwargs):
        from django_statsd.clients import statsd

        statsd.incr('xiaolumm.ninepic_count')

        advers = []
        now = datetime.datetime.now()

        from flashsale.xiaolumm import util_emoji

        for adver in self.get_today_queryset().order_by('-start_time'):
            if now >= adver.start_time:
                model_id = None
                if adver.detail_modelids:
                    model_ids = adver.detail_modelids.split(',')
                    model_id = random.choice(model_ids)
                mama_link = self.get_mama_link(request, model_id=model_id)

                adver.description = util_emoji.match_emoji(adver.description)

                adver.description += mama_link

                advers.append(adver)
        serializer = self.get_serializer(advers, many=True)

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

