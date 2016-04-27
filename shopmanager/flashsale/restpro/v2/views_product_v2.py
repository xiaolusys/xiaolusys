# -*- coding:utf-8 -*-
import json
import datetime
import hashlib
import urlparse
import random
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.forms import model_to_dict

from rest_framework import generics
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions
from rest_framework_extensions.cache.decorators import cache_response


from flashsale.pay.models import GoodShelf, ModelProduct


from . import serializers


CACHE_VIEW_TIMEOUT = 30

class PosterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ###特卖海报API：
    - {prefix}/today[.format]: 获取今日特卖海报;
    - {prefix}/previous[.format]: 获取昨日特卖海报;
    """
    queryset = GoodShelf.objects.filter(is_active=True)
    serializer_class = serializers.PosterSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def calc_porter_cache_key(self, view_instance, view_method,
                              request, args, kwargs):
        key_vals = ['days']
        key_maps = kwargs or {}
        for k, v in request.GET.copy().iteritems():
            if k in key_vals and v.strip():
                key_maps[k] = v

        return hashlib.sha1(u'.'.join([
            view_instance.__module__,
            view_instance.__class__.__name__,
            view_method.__name__,
            json.dumps(key_maps, sort_keys=True).encode('utf-8')
        ])).hexdigest()

    def get_latest_right_date(self, dt):
        ldate = dt
        model_qs = self.get_queryset()
        for i in xrange(0, 30):
            ldate = dt - datetime.timedelta(days=i)
            product_qs = model_qs.filter(active_time__year=ldate.year,
                                         active_time__month=ldate.month,
                                         active_time__day=ldate.day)
            if product_qs.count() > 0:
                break
        return ldate

    def get_today_poster(self):
        target_date = self.get_latest_right_date(datetime.date.today())
        posters = self.queryset.filter(active_time__year=target_date.year,
                                       active_time__month=target_date.month,
                                       active_time__day=target_date.day)
        return posters.count() and posters[0] or None

    def get_previous_poster(self):
        target_date = datetime.date.today() - datetime.timedelta(days=1)
        target_date = self.get_latest_right_date(target_date)
        posters = self.queryset.filter(active_time__year=target_date.year,
                                       active_time__month=target_date.month,
                                       active_time__day=target_date.day)
        return posters.count() and posters[0] or None

    def get_future_poster(self, request):
        view_days = int(request.GET.get('days', '1'))
        target_date = datetime.date.today() + datetime.timedelta(days=view_days)
        target_date = self.get_latest_right_date(target_date)
        posters = self.queryset.filter(active_time__year=target_date.year,
                                       active_time__month=target_date.month,
                                       active_time__day=target_date.day)
        return posters.count() and posters[0] or None

    def list(self, request, *args, **kwargs):
        raise exceptions.APIException(u'该接口暂未实现')

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_porter_cache_key')
    @list_route(methods=['get'])
    def today(self, request, *args, **kwargs):
        poster = self.get_today_poster()
        serializer = self.get_serializer(poster, many=False)
        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_porter_cache_key')
    @list_route(methods=['get'])
    def previous(self, request, *args, **kwargs):
        poster = self.get_previous_poster()
        serializer = self.get_serializer(poster, many=False)
        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_porter_cache_key')
    @list_route(methods=['get'])
    def preview(self, request, *args, **kwargs):
        poster = self.get_future_poster(request)
        serializer = self.get_serializer(poster, many=False)
        return Response(serializer.data)