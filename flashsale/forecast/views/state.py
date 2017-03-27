# coding: utf8
from __future__ import absolute_import, unicode_literals

import os
import json
import datetime
from collections import  defaultdict

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions
from rest_framework import filters
import django_filters


from ..models import (
    ForecastStats
)
from .. import serializers

import logging
logger = logging.getLogger(__name__)

CACHE_VIEW_TIMEOUT = 30


class ForecastStatsFilter(filters.FilterSet):
    purchase_time_start = django_filters.DateTimeFilter(name="purchase_time", lookup_type='gte')
    purchase_time_end = django_filters.DateTimeFilter(name="purchase_time", lookup_type='lte')

    class Meta:
        model = ForecastStats
        fields = ['purchase_time_start', 'purchase_time_end']

class ForecastStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ForecastStats.objects.exclude(status=ForecastStats.CLOSED)
    authentication_classes = (authentication.BasicAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.ForecastStatsSerializer
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer, renderers.TemplateHTMLRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    # filter_fields = ('supplier', 'purchase_time', 'buyer_name', 'purchaser')
    # filter_class = ForecastStatsFilter
    template_name = 'forecast/report_stats.html'

    def list(self, request, format=None, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset()).select_related('supplier')
        start_time = request.GET.get('start_time')
        end_time   = request.GET.get('end_time')
        action = request.GET.get('action')
        if not start_time:
            start_time = datetime.datetime(2016, 6, 1)
        if not end_time:
            end_time = datetime.datetime.now()
        if action == 'arrival_time':
            queryset = queryset.filter(arrival_time__range=(start_time,end_time))
        elif action == 'forecast_time':
            queryset = queryset.filter(forecast_inbound__forecast_arrive_time__range=(start_time, end_time))
        else:
            action = 'purchase_time'
            queryset = queryset.filter(purchase_time__range=(start_time, end_time))

        stats_values = queryset.extra(
            tables=('forecast_inbound','forecast_stats'),
            where=('forecast_stats.forecast_inbound_id = forecast_inbound.id',),
            select = {
                'arrival_period': 'IFNULL(TIMESTAMPDIFF(DAY, forecast_stats.purchase_time, forecast_stats.arrival_time),TIMESTAMPDIFF(DAY, forecast_stats.purchase_time,NOW()))',
                'delivery_period': 'IFNULL(TIMESTAMPDIFF(DAY, forecast_stats.purchase_time, forecast_stats.delivery_time),TIMESTAMPDIFF(DAY, forecast_stats.purchase_time,NOW()))',
                'logistic_period': 'TIMESTAMPDIFF(DAY, forecast_stats.delivery_time, forecast_stats.arrival_time)',
                'forecast_arrive_time': 'IFNULL(DATE_FORMAT(forecast_inbound.forecast_arrive_time, "%%Y-%%m-%%d"),"-")',
                'purchase_time': 'IFNULL(DATE_FORMAT(forecast_stats.purchase_time, "%%Y-%%m-%%d"),"-")',
                'delivery_time': 'IFNULL(DATE_FORMAT(forecast_stats.delivery_time, "%%Y-%%m-%%d"),"-")',
                'arrival_time': 'IFNULL(DATE_FORMAT(forecast_stats.arrival_time, "%%Y-%%m-%%d"),"-")',
                'is_lack': 'forecast_stats.has_lack',
                'is_defact': 'forecast_stats.has_defact',
                'is_overhead': 'forecast_stats.has_overhead',
                'is_wrong': 'forecast_stats.has_wrong',
                'is_unrecord': 'forecast_stats.is_unrecordlogistic',
                'is_timeouted': 'forecast_stats.is_timeout',
                'is_close': 'forecast_stats.is_lackclose',
            }
        ).select_related('forecast_inbound').values(
            'id', 'forecast_inbound_id', 'supplier__supplier_name', 'buyer_name', 'purchaser', 'purchase_num',
            'inferior_num', 'lack_num', 'purchase_amount', 'arrival_period', 'delivery_period', 'logistic_period',
            'forecast_arrive_time', 'purchase_time', 'delivery_time', 'arrival_time',
            'is_lack', 'is_defact', 'is_overhead', 'is_wrong', 'is_unrecord', 'is_timeouted', 'is_close','status'
        )

        order_values_list = queryset.values_list('id', 'forecast_inbound__relate_order_set')
        order_values_dict = defaultdict(list)
        for id, order_id in order_values_list:
            order_values_dict[id].append(order_id)

        stats_values_list = []
        for stats in stats_values:
            stats['supplier_name'] = stats.pop('supplier__supplier_name')
            stats['relate_orders'] = ','.join([str(s) for s in order_values_dict.get(stats['id'])])
            stats_values_list.append(stats)

        if format == 'json':
            return Response({'results': stats_values_list,
                             'start_time':start_time,
                             'end_time':end_time,
                             'action': action})
        else:
            stats_values = list(stats_values)
            return Response({'results': stats_values_list,
                             'start_time':start_time,
                             'end_time':end_time,
                             'action': action})

