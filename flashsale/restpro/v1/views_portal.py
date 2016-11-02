# -*- coding:utf-8 -*-
import json
import datetime
import hashlib

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions
from rest_framework_extensions.cache.decorators import cache_response


from flashsale.pay.models import GoodShelf, BrandEntry, BrandProduct

from . import serializers

CACHE_VIEW_TIMEOUT = 60

class PortalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ###商城入口API(包含海报,类目,活动,及品牌推广)：
    """
    queryset = GoodShelf.objects.filter(is_active=True)
    serializer_class = serializers.PortalSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

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
        target_date = datetime.datetime.now()
        poster = self.queryset.filter(active_time__lte=target_date).order_by('-active_time').first()
        return poster

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_porter_cache_key')
    def list(self, request, *args, **kwargs):
        poster = self.get_today_poster()
        serializer = self.get_serializer(poster, many=False)
        return Response(serializer.data)


class BrandProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ###品牌商品入口：
    - {prefix}/list[.format]: 获取品牌商品列表;
    """
    queryset = BrandProduct.objects.all()
    serializer_class = serializers.BrandProductSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def list(self, request, brand_id, *args, **kwargs):
        """
        品牌商品列表
        """
        qs = self.queryset.filter(brand_id=brand_id)
        queryset = self.filter_queryset(qs)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BrandEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """
     ###品牌入口：
    - {prefix}/list[.format]: 获取品牌列表;
    - {prefix}/{brand_id}/products[.format]: 获取品牌商品列表;
    """
    queryset = BrandEntry.objects.all()
    serializer_class = serializers.BrandEntrySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_queryset(self):
        return self.queryset.filter(is_active=True)


