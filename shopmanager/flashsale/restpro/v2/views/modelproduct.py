# -*- coding:utf-8 -*-
import os
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
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework_extensions.cache.decorators import cache_response

from shopback.items.models import Product
from flashsale.pay.models import ModelProduct

from flashsale.restpro.v2 import serializers as serializers_v2

import logging
logger = logging.getLogger('service.restpro')

CACHE_VIEW_TIMEOUT = 30

class ModelProductV2ViewSet(viewsets.ReadOnlyModelViewSet):
    """
        ## 特卖商品(聚合)列表API：
        - Model:
            * `{
                "id": 商品ID,
                "name": 商品名称,
                "category_id": 类目id,
                "lowest_agent_price": 最低出售价,
                "lowest_std_sale_price": 标准出售价,
                "is_saleout": 是否售光,
                "is_favorite": 是否收藏,
                "sale_state": 在售状态(will:即将开售,　on:在售, off:下架),
                "head_img": 头图,
                "web_url": app商品详情链接,
                "watermark_op": 水印参数(拼接方法: head_img?watermark_op|其它图片参数)
              }`
        ***
        - [获取特卖商品列表: /rest/v2/modelproducts](/rest/v2/modelproducts)
            * 查询参数: cid = 类目cid
        - [今日特卖: /rest/v2/modelproducts/today](/rest/v2/modelproducts/today)
        - [昨日特卖: /rest/v2/modelproducts/yesterday](/rest/v2/modelproducts/yesterday)
        - [即将上新: /rest/v2/modelproducts/tomorrow](/rest/v2/modelproducts/tomorrow)
    """
    queryset = ModelProduct.objects.all()
    serializer_class = serializers_v2.SimpleModelProductSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    paginate_by = 10
    page_query_param = 'page'

    def calc_items_cache_key(self, view_instance, view_method,
                             request, args, kwargs):
        key_vals = ['order_by', 'id', 'pk', 'model_id', 'days', 'page', 'page_size']
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

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    def retrieve(self, request, *args, **kwargs):
        """ 获取用户订单及订单明细列表 """
        instance = self.get_object()
        data = serializers_v2.ModelProductSerializer(instance, context={'request': request}).data
        return Response(data)

    def order_queryset(self, request, queryset, order_by=None):
        """ 对集合列表进行排序 """
        order_by = order_by or request.REQUEST.get('order_by')
        if order_by == 'price':
            queryset = queryset.order_by('agent_price')
        else:
            queryset = queryset.extra(#select={'is_saleout': 'remain_num - lock_num <= 0'},
                                      order_by=['salecategory__sort_order', '-is_recommend', '-order_weight', '-id'])
        return queryset

    def get_normal_qs(self, queryset):
        return queryset.filter(status=ModelProduct.NORMAL, is_topic=False)

    def list(self, request, *args, **kwargs):

        cid  = request.GET.get('cid')
        logger.info({'stype': 'modelproduct' ,
                     'path': request.get_full_path(),
                     'cid': cid,
                     'buyer': request.user and request.user.id or 0})
        queryset = self.filter_queryset(self.get_queryset())
        onshelf_qs = self.get_normal_qs(queryset).filter(shelf_status=ModelProduct.ON_SHELF)
        if cid:
            onshelf_qs = onshelf_qs.filter(salecategory__cid__startswith=cid)

        page = self.paginate_queryset(onshelf_qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def get_pagination_response_by_date(self, request, cur_date, only_upshelf=True):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.get_normal_qs(queryset)
        date_range = (datetime.datetime.combine(cur_date, datetime.time.min),
                      datetime.datetime.combine(cur_date, datetime.time.max))
        if only_upshelf:
            queryset = queryset.filter(
                Q(onshelf_time__range=date_range) | Q(is_recommend=True),
                shelf_status=ModelProduct.ON_SHELF
            )
        else:
            queryset = queryset.filter(
                onshelf_time__range=date_range
            )
        # queryset = self.order_queryset(request, tal_queryset, order_by=self.INDEX_ORDER_BY)

        pagin_query = self.paginate_queryset(queryset)
        object_list = self.get_serializer(pagin_query, many=True).data
        response = self.get_paginated_response(object_list)
        response.data.update({
            'offshelf_deadline': object_list and max([obj['offshelf_time'] for obj in object_list]) or None,
            'onshelf_starttime': object_list and min([obj['onshelf_time'] for obj in object_list]) or None
        })
        return response

    def get_lastest_date(self, cur_date, predict=False):
        """ 获取今日上架日期 """
        dt_start = datetime.datetime.combine(cur_date, datetime.time.max)
        if predict:
            first_product = self.queryset.filter(onshelf_time__gte=dt_start)\
                .order_by('-onshelf_time').first()
        else:
            first_product = self.queryset.filter(onshelf_time__lte=dt_start) \
                .order_by('-onshelf_time').first()
        return first_product and first_product.onshelf_time.date() or datetime.date.today()

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def today(self, request, *args, **kwargs):
        """ 今日商品列表分页接口 """
        logger.info({'stype': 'modelproduct',
                     'path': request.get_full_path(),
                     'buyer': request.user and request.user.id or 0})
        today_dt = self.get_lastest_date(datetime.date.today())
        return self.get_pagination_response_by_date(request, today_dt, only_upshelf=True)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def yesterday(self, request, *args, **kwargs):
        """ 昨日特卖列表分页接口 """
        logger.info({'stype': 'modelproduct',
                     'path': request.get_full_path(),
                     'buyer': request.user and request.user.id or 0})
        yesterday_dt = self.get_lastest_date(datetime.date.today() - datetime.timedelta(days=1))
        return self.get_pagination_response_by_date(request, yesterday_dt, only_upshelf=False)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def tomorrow(self, request, *args, **kwargs):
        """ 昨日特卖列表分页接口 """
        logger.info({'stype': 'modelproduct',
                     'path': request.get_full_path(),
                     'buyer': request.user and request.user.id or 0})
        tomorrow_dt = self.get_lastest_date(datetime.date.today() + datetime.timedelta(days=1), predict=True)
        return self.get_pagination_response_by_date(request, tomorrow_dt, only_upshelf=False)

