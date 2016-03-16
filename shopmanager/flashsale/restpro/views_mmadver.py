# coding=utf-8
import json, os, settings
from flashsale.xiaolumm.models_advertis import XlmmAdvertis, NinePicAdver
import datetime
from rest_framework import viewsets, permissions, authentication, renderers
from rest_framework.response import Response
from . import serializers
from flashsale.pay.models import Customer
from django.shortcuts import get_object_or_404
from flashsale.xiaolumm.models import XiaoluMama
from rest_framework import exceptions

from django.forms import model_to_dict


class XlmmAdvertisViewSet(viewsets.ModelViewSet):
    """
    ### 特卖平台－代理公告API:
    - {prefix}[.format] method:get : 获取登陆用户的代理公告
    """
    queryset = XlmmAdvertis.objects.all()
    serializer_class = serializers.XlmmAdvertisSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

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
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_today_queryset(self):
        yesetoday = datetime.date.today() - datetime.timedelta(days=1)
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        queryset = self.queryset.filter(start_time__gte=yesetoday, start_time__lt=tomorrow)
        return queryset

    def get_mama_link(self, request):
        """
        获取代理专属链接
        """
        customer = Customer.objects.get(user=request.user)
        xlmm = customer.getXiaolumm()
        if xlmm:
            return os.path.join(settings.M_SITE_URL, "m/{}/".format(xlmm.id))  # 专属链接
        else:
            return ''

    def list(self, request, *args, **kwargs):
        advers = []
        now = datetime.datetime.now()
        for adver in self.get_today_queryset().order_by('-start_time'):
            if now >= adver.start_time:
                mama_link = self.get_mama_link(request)
                adver.description += mama_link
                advers.append(adver)
        serializer = self.get_serializer(advers, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException("方法不允许")

