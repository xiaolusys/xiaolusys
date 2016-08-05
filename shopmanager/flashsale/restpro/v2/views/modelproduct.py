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
        - 获取特卖商品详情: /rest/v2/modelproducts/[modelproduct_id]

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
            queryset = queryset.extra(select={'is_saleout': 'remain_num - lock_num <= 0'},
                                      order_by=['category__sort_order','is_saleout', '-details__is_recommend',
                                                '-details__order_weight', '-id'])
        return queryset

    def get_normal_qs(self, queryset):
        return queryset.filter(status=ModelProduct.NORMAL, is_topic=False)

    def list(self, request, *args, **kwargs):
        category_id  = request.GET.get('category_id')
        if category_id and not category_id.isdigit():
            raise exceptions.APIException(u'非法的类目ID')

        queryset = self.filter_queryset(self.get_queryset())
        onshelf_qs = self.get_normal_qs(queryset).filter(shelf_status=ModelProduct.ON_SHELF)
        if category_id:
            onshelf_qs = onshelf_qs.filter(salecategory=category_id)

        page = self.paginate_queryset(onshelf_qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

