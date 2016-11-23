# -*- coding:utf-8 -*-
import json
import datetime
import hashlib
import random
from django.shortcuts import get_object_or_404, Http404
from django.db.models import Q
from django.core.urlresolvers import reverse

from rest_framework import filters
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework_extensions.cache.decorators import cache_response

from core import pagination
from flashsale.pay.models import ModelProduct, Customer, CuShopPros

from flashsale.restpro.v2 import serializers as serializers_v2
from flashsale.pay.apis.v1.product import get_virtual_modelproducts
from apis.v1.products import ModelProductCtl, SkustatCtl

import logging
logger = logging.getLogger(__name__)

CACHE_VIEW_TIMEOUT = 30


class ModelProductFilter(filters.FilterSet):
    class Meta:
        model = ModelProduct


class ModelProductV2ViewSet(viewsets.ReadOnlyModelViewSet):
    """
        ## 特卖商品(聚合)列表API：
        ## Model:
            {
                "id": 商品ID,
                "name": 商品名称,
                "category_id": 类目id,
                "lowest_agent_price": 最低出售价,
                "lowest_std_sale_price": 标准出售价,
                "is_saleout": 是否售光,
                "sale_state": 在售状态(will:即将开售,　on:在售, off:下架),
                "head_img": 头图,
                "web_url": app商品详情链接,
                "watermark_op": 水印参数(拼接方法: head_img?watermark_op|其它图片参数)
            }
        ***
        ## [获取特卖商品列表: /rest/v2/modelproducts](/rest/v2/modelproducts)
            查询参数:
                cid: cid1,cid2
                order_by: price - 按价格排序 (默认按推荐排序)
        ## [今日特卖: /rest/v2/modelproducts/today](/rest/v2/modelproducts/today)
        ## [昨日特卖: /rest/v2/modelproducts/yesterday](/rest/v2/modelproducts/yesterday)
        ## [即将上新: /rest/v2/modelproducts/tomorrow](/rest/v2/modelproducts/tomorrow)
        ## [获取商品头图: /rest/v2/modelproducts/get_headimg](/rest/v2/modelproducts/get_headimg)
        ## [妈妈选品佣金: /rest/v2/modelproducts/product_choice](/rest/v2/modelproducts/product_choice)
    """
    queryset = ModelProduct.objects.all()
    serializer_class = serializers_v2.SimpleModelProductSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
    pagination_class = pagination.PageNumberPkPagination
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = ModelProductFilter
    paginate_by = 10
    page_query_param = 'page'

    def paginate_pks(self, queryset, pk_alias='id'):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_pks(queryset, self.request, view=self, pk_alias=pk_alias)

    def calc_items_cache_key(self, view_instance, view_method,
                             request, args, kwargs):
        key_vals = ['order_by', 'id', 'pk', 'model_id', 'cid', 'days', 'page', 'page_size', 'modelId']
        key_maps = kwargs or {}
        for k, v in request.GET.copy().iteritems():
            if k in key_vals and v.strip():
                key_maps[k] = v
        return hashlib.sha1(u'.'.join([
            view_instance.__module__,
            view_instance.__class__.__name__,
            view_method.__name__,
            json.dumps(key_maps, sort_keys=True)
        ])).hexdigest()

    # @cache_response(timeout=10, key_func='calc_items_cache_key')
    def retrieve(self, request, *args, **kwargs):
        """ 获取用户订单及订单明细列表, 因为包含用户定制信息，该接口 """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        from apis.v1.products import ModelProductCtl
        obj = ModelProductCtl.retrieve(self.kwargs[lookup_url_kwarg])
        data = serializers_v2.APIModelProductSerializer(obj, context={'request': request}).data
        #data = serializers_v2.ModelProductSerializer(instance, context={'request': request}).data
        return Response(data)

    def order_queryset(self, queryset, order_by=None):
        """ 对集合列表进行排序 """
        if order_by == 'portal':
            queryset = queryset.extra(  # select={'is_saleout': 'remain_num - lock_num <= 0'},
                order_by=['-salecategory__sort_order', '-is_recommend', '-order_weight', '-id'])
        elif order_by == 'price':
            queryset = queryset.order_by('lowest_agent_price')
        else:
            queryset = queryset.extra(  # select={'is_saleout': 'remain_num - lock_num <= 0'},
                order_by=['-is_recommend', '-order_weight', '-id'])
        return queryset

    def get_normal_qs(self, queryset):
        return queryset.filter(status=ModelProduct.NORMAL, is_topic=False)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    def list(self, request, *args, **kwargs):
        cid_str  = request.GET.get('cid','')
        order_by = request.GET.get('order_by')
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.order_queryset(queryset, order_by=order_by)
        onshelf_qs = queryset.filter(shelf_status=ModelProduct.ON_SHELF)
        q_filter = Q()
        cids = [c for c in cid_str.split(',') if c]
        for cid in cids:
            q_filter = q_filter | Q(salecategory__cid__startswith=cid)

        onshelf_qs = onshelf_qs.filter(q_filter)
        page_ids = self.paginate_pks(onshelf_qs)
        modelproducts = ModelProductCtl.multiple(ids=page_ids)
        serializer = serializers_v2.APIModelProductListSerializer(modelproducts, many=True)
        return self.get_paginated_response(serializer.data)

    def get_pagination_response_by_date(self, request, cur_date, only_onshelf=False):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.get_normal_qs(queryset)

        queryset = self.order_queryset( queryset, order_by='portal')
        date_range = (datetime.datetime.combine(cur_date, datetime.time.min),
                      datetime.datetime.combine(cur_date, datetime.time.max))
        if only_onshelf:
            queryset = queryset.filter(
                Q(onshelf_time__range=date_range),
                shelf_status=ModelProduct.ON_SHELF
            )
        else:
            queryset = queryset.filter(
                onshelf_time__range=date_range
            )
        # queryset = self.order_queryset(request, tal_queryset, order_by=self.INDEX_ORDER_BY)

        page_ids = self.paginate_pks(queryset)
        modelproducts = ModelProductCtl.multiple(ids=page_ids)
        object_list = serializers_v2.APIModelProductListSerializer(modelproducts, many=True).data
        response    = self.get_paginated_response(object_list)
        onshelf_time    = object_list and max([obj['offshelf_time'] for obj in object_list]) or datetime.datetime.now()
        offshelf_time   = object_list and min([obj['onshelf_time'] for obj in object_list])
        if not offshelf_time:
            offshelf_time = onshelf_time + datetime.timedelta(seconds= 60 * 60 * 28)
        response.data.update({
            'offshelf_deadline': onshelf_time,
            'onshelf_starttime': offshelf_time
        })
        return response

    def get_lastest_date(self, cur_date, predict=False, only_onshelf=False):
        """ 获取今日上架日期 """
        queryset = self.queryset
        if not predict:
            queryset = self.queryset.filter(is_topic=False)

        if only_onshelf:
            queryset = queryset.filter(shelf_status=ModelProduct.ON_SHELF)

        if predict:
            dt_start = datetime.datetime.combine(cur_date, datetime.time.min)
            queryset = queryset.filter(onshelf_time__gte=dt_start).order_by('onshelf_time')
        else:
            dt_start = datetime.datetime.combine(cur_date, datetime.time.max)
            queryset = queryset.filter(onshelf_time__lte=dt_start).order_by('-onshelf_time')

        first_obj = queryset.only('onshelf_time').first()
        return first_obj and first_obj.onshelf_time.date() or datetime.date.today()

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def today(self, request, *args, **kwargs):
        """ 今日商品列表分页接口 """
        today_dt = self.get_lastest_date(datetime.date.today(), only_onshelf=True)
        return self.get_pagination_response_by_date(request, today_dt, only_onshelf=True)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def yesterday(self, request, *args, **kwargs):
        """ 昨日特卖列表分页接口 """
        yesterday_dt = self.get_lastest_date(datetime.date.today() - datetime.timedelta(days=1))
        return self.get_pagination_response_by_date(request, yesterday_dt, only_onshelf=False)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def tomorrow(self, request, *args, **kwargs):
        """ 昨日特卖列表分页接口 """
        tomorrow_dt = self.get_lastest_date(datetime.date.today() + datetime.timedelta(days=1), predict=True)
        return self.get_pagination_response_by_date(request, tomorrow_dt, only_onshelf=False)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def get_headimg(self, request, *args, **kwargs):
        """ 查询头图接口 """
        modelId = request.GET.get('modelId', '')
        if not modelId.isdigit():
            raise Http404
        from apis.v1.products import ModelProductCtl
        obj = ModelProductCtl.retrieve(modelId)
        data = serializers_v2.APIModelProductListSerializer(obj).data
        return Response([data])


    @list_route(methods=['get'])
    def product_choice(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            raise Http404

        sort_field = request.GET.get('sort_field') or 'id'  # 排序字段
        parent_cid = request.GET.get('cid') or 0
        reverse = request.GET.get('reverse') or 0
        customer = get_object_or_404(Customer, user=request.user)
        mama = customer.get_charged_mama()

        reverse = int(reverse) if str(reverse).isdigit() else 0
        # model_ids = list(CuShopPros.objects.filter(
        #     customer=customer.id,
        #     pro_status=CuShopPros.UP_SHELF).values_list("model", flat=True))
        queryset = self.queryset.filter(shelf_status=ModelProduct.ON_SHELF,
                                        status=ModelProduct.NORMAL)
        if parent_cid:
            queryset = queryset.filter(salecategory__parent_cid=parent_cid)

        product_ids = list(queryset.values_list('id', flat=True))
        model_products = ModelProductCtl.multiple(ids=product_ids)

        next_mama_level_info = mama.next_agencylevel_info()
        for md in model_products:
            rebate_scheme = md.get_rebetaschema()
            lowest_agent_price = md.detail_content['lowest_agent_price']
            rebet_amount = rebate_scheme.calculate_carry(mama.agencylevel, lowest_agent_price)

            total_remain_num = sum([len(p.sku_ids) for p in md.get_products()]) * 30
            sale_num = total_remain_num * 19 + random.randint(1,19)

            next_rebet_amount = rebate_scheme.calculate_carry(next_mama_level_info[0], lowest_agent_price) or 0.0
            md.sale_num = sale_num
            md.rebet_amount = rebet_amount
            md.next_rebet_amount = next_rebet_amount

        if sort_field in ['id', 'sale_num', 'rebet_amount', 'lowest_std_sale_price', 'lowest_agent_price']:
            model_products = sorted(model_products, key=lambda k: getattr(k, sort_field), reverse=reverse)

        object_list = self.paginate_queryset(model_products)
        serializer = serializers_v2.APIMamaProductListSerializer(
            object_list, many=True,
            context={'request': request,
                     'mama': mama,
                     "shop_product_num": len(object_list)})
        return self.get_paginated_response(serializer.data)

    @list_route(methods=['get'])
    def electronic_goods(self, request, *args, **kwargs):
        """ electronic商品列表分页接口 """
        queryset = ModelProduct.objects.filter(product_type=1)
        object_list = serializers_v2.ModelProductSerializer(queryset, context={'request': request}, many=True).data
        response = Response(object_list)
        return response

    @list_route(methods=['get'])
    def boutique(self, request, *args, **kwargs):
        # type : (HttpRequest, *Any, **Any) -> HttpResponse
        """精品券接口(虚拟商品)
        """
        queryset = get_virtual_modelproducts()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers_v2.BoutiqueModelProductSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
