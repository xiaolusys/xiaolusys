# coding:utf-8
import json
import hashlib

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

from supplychain.supplier.models import SaleCategory
from .. import serializers

CACHE_VIEW_TIMEOUT = 30

class SaleCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
        ## 特卖选品类目API：
        - Model:
            * `{
                "id": 款式ID,
                "grade": 类目等级,
                "cat_pic": 展示图,
                "parent_cid": 父ID,
                "name": 类目名,
                "cid": 类目ID
              }`
        ***
        - [获取类目信息列表: /rest/v2/categorys](/rest/v2/categorys)
        - [获取类目最新版本信息: /rest/v2/categorys/latest_version](/rest/v2/categorys/latest_version)
            * `{
                "version": 版本号,
                "download_url": 下载链接,
                "sha1": sha1值
            }`
    """
    queryset = SaleCategory.objects.all()
    serializer_class = serializers.SaleCategorySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    paginate_by = 1
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
    def list(self, request, *args, **kwargs):
        """ 获取用户订单及订单明细列表 """
        category_data = SaleCategory.get_salecategory_jsontree()
        return Response(category_data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    def retrieve(self, request, *args, **kwargs):
        """ 获取用户订单及订单明细列表 """
        instance = self.get_object()
        data = self.get_serializer(instance, context={'request': request}).data
        return Response(data)

    @list_route(methods=['get'])
    def latest_version(self, request, *args, **kwargs):
        version = SaleCategory.latest_version()
        return Response(version)