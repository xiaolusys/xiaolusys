# coding=utf-8
import datetime
import logging
import os
import time
import urlparse

from django.conf import settings
from django.db.models import Sum, Count
from django_statsd.clients import statsd
from django.shortcuts import get_object_or_404
from rest_framework import authentication
from core import xlmm_rest_exceptions as exceptions
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework.views import APIView

from flashsale.pay.models import Customer
from flashsale.xiaolumm.models import XiaoluMama, MamaMission, MamaMissionRecord
from flashsale.xiaolumm import serializers


class MamaMissionRecordViewset(viewsets.ModelViewSet):
    """
    ## 妈妈新手任务API:
    > ## 周任务信息列表 [/rest/v2/mama/mission/weeklist](/rest/v2/mama/mission/weeklist):
        - 参数 : year_week = 2016-34 (年-周)
        - ``` {
            "staging_award_count": 待完成任务总奖励,
            "staging_award_amount": 待完成任务数,
            "personal_missions": []# 个人任务
            "group_missions": []# 团队任务
          }```
    """
    queryset = MamaMissionRecord.objects.all()
    serializer_class = serializers.MamaMissionRecordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_xiaolumama(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xiaolumama = get_object_or_404(XiaoluMama, openid=customer.unionid)
        return xiaolumama

    def list(self, request, *args, **kwargs):
        raise exceptions.APIException(u'该接口暂未提供数据')

    @list_route(methods=['get'])
    def weeklist(self, request, *args, **kwargs):

        year_week   = request.GET.get('year_week', datetime.datetime.now().strftime('%Y-%W'))
        xiaolumama  = self.get_xiaolumama(request)
        queryset    = self.get_queryset().filter(mama_id=xiaolumama.id, year_week=year_week)

        personal_missions = queryset.filter(mission__target=MamaMission.TARGET_PERSONAL)
        group_missions    = queryset.filter(mission__target=MamaMission.TARGET_GROUP)
        staging_awards_list = queryset.filter(status=MamaMissionRecord.STAGING)\
            .values_list('award_amount', flat=True)

        response_data = {
            'staging_award_count': len(staging_awards_list),
            'staging_award_amount': sum(staging_awards_list),
            'personal_missions': self.get_serializer(personal_missions, many=True).data,
            'group_missions': self.get_serializer(group_missions, many=True).data
        }

        return Response(response_data)


