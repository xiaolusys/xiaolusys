# -*- coding:utf-8 -*-
import datetime
import hashlib
import json
import os
import random
import urlparse

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms import model_to_dict
from django.shortcuts import get_object_or_404
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework import generics
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework_extensions.cache.decorators import cache_response
from flashsale.pay.models import GoodShelf, BrandProduct, Customer
from flashsale.promotion.models import ActivityEntry
from flashsale.xiaolumm.models import XiaoluMama, MamaTabVisitStats
from flashsale.mmexam.models import DressProduct
from core.options import log_action, ADDITION, CHANGE
from flashsale.pay.models import CustomerShops, CuShopPros
from flashsale.xiaolumm.models.models_rebeta import AgencyOrderRebetaScheme
from shopback.items.models import Product
from flashsale.restpro import constants
from flashsale.restpro.v1 import serializers

import logging
logger = logging.getLogger('django.request')

CACHE_VIEW_TIMEOUT = 30


class PosterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ###特卖海报API：
    * 获取今日特卖海报: [/rest/v1/posters/today](/rest/v1/posters/today);
    * 获取昨日特卖海报: [/rest/v1/posters/previous](/rest/v1/posters/previous);
    """
    queryset = GoodShelf.objects.filter(is_active=True)
    serializer_class = serializers.PosterSerializer
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
        raise exceptions.APIException(u'该接口暂未提供数据')

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


class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ###特卖活动API：
    > ### /{pk}/get_share_params: 获取活动分享参数;
    > ### /startup_diagrams :获取启动图片；
    """
    queryset = ActivityEntry.objects.all()
    serializer_class = serializers.ActivityEntrySerializer
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

    #     @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_porter_cache_key')
    def list(self, request, *args, **kwargs):
        now = datetime.datetime.now()
        queryset = self.queryset.filter(is_active=True,end_time__gte=now)\
                                .exclude(act_type=ActivityEntry.ACT_MAMA)\
                                .order_by('-order_val', '-modified')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_random_title(self):
        n = int(random.random() * 3) % 3
        return constants.PYQ_TITLES[n], n

    def get_share_link(self, params):
        link = urlparse.urljoin(settings.M_SITE_URL, constants.SHARE_LINK)
        return link.format(**params)

    def get_qrcode_page_link(self, *args, **kwargs):
        qrcode_link = reverse('qrcode_view')
        if kwargs.has_key('mama_id'):
            rev_url = qrcode_link + '?mama_id={mama_id}'  # 添加mama_id
            qrcode_link = rev_url.format(**kwargs)
        return urlparse.urljoin(settings.M_SITE_URL, qrcode_link)


    @list_route(methods=['get'])
    def get_all_events(self, request, *args, **kwargs):
        now = datetime.datetime.now()
        queryset = self.queryset.filter(is_active=True,end_time__gte=now)\
                                .order_by('-order_val', '-modified')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
        
    @detail_route(methods=['get'])
    def get_share_params(self, request, *args, **kwargs):
        """ 获取活动分享参数 """
        active_obj = self.get_object()

        params = {}
        # if active_obj.login_required:
        if request.user and request.user.is_authenticated():
            customer = get_object_or_404(Customer, user=request.user.id)
            params.update({'customer': customer})
            mama = customer.get_charged_mama()
            if mama:
                params.update({'mama_id': mama.id})
            else:
                params.update({'mama_id': 1})
        if not params:
            params.update({'customer': {},'mama_id': 1})

        share_params = active_obj.get_shareparams(**params)
        share_params.update(qrcode_link=self.get_qrcode_page_link(**params))
        return Response(share_params)

    @list_route(methods=['get'])
    def startup_diagrams(self, request, *args, **kwargs):
        """ app首页启动图 """

        return Response({
            'picture': '',
            'created': datetime.datetime.now(),
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_data = serializers.ActivityEntrySerializer(instance).data
        return Response(serializer_data)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ## __特卖商品API__：
    * 最新版本: [/rest/v2/products](/rest/v2/products)
    ---
    > ### /promote_today[.format]: 获取今日推荐商品列表;
    > ### /promote_previous[.format]: 获取昨日推荐商品列表;
    > ### /promote_today_paging：获取今日推荐商品分页列表;
      - `page`:页码（０开始）
      - `page_size`：每页数量初始为10
    > ### /promote_previous_paging：获取昨日推荐商品分页列表;
      - `page`:页码（０开始）
      - `page_size`：每页数量初始为10
    > ### /childlist[.format]: 获取童装专区商品列表;
    > ### /ladylist[.format]: 获取女装专区商品列表;
    > ### /previous[.format]: 获取昨日特卖商品列表;
    > ### /advance[.format]: 获取明日特卖商品列表;
    > ### /seckill[.format]: 获取秒杀商品列表;
    > ### /modellist/{model_id}[.format]:获取聚合商品列表（model_id:款式ID）;
    > ### /{pk}/details[.format]: 商品详情;
    > ### /{pk}/snapshot.html: 获取特卖商品快照（需登录）;
    > ### /my_choice_pro: 获取'我的选品列表'产品数据
           params: category=[1,2]
           sort_field= ['id', 'sale_num', 'rebet_amount', 'std_sale_price', 'agent_price']
           page=n (n >= 1)
           page_size=n (n >= 1)
    """
    queryset = Product.objects.all()
    serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    paginate_by = 10
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 20
    INDEX_ORDER_BY = 'main'

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

    def list(self, request, *args, **kwargs):
        raise exceptions.APIException(u'该接口暂未提供数据')

    @list_route(methods=['get'])
    def get_product_by_model_id(self, request, *args, **kwargs):
        model_id = request.REQUEST.get('model_id') or None
        pros = self.queryset.filter(model_id=model_id, status='normal')
        serializer = self.get_serializer(pros, many=True)
        return Response(serializer.data)

    def get_latest_right_date(self, dt):
        ldate = dt
        model_qs = self.get_queryset().filter(shelf_status=Product.UP_SHELF)
        for i in xrange(0, 30):
            ldate = dt - datetime.timedelta(days=i)
            product_qs = model_qs.filter(sale_time=ldate)
            if product_qs.count() > 0:
                break
        return ldate

    def get_preview_right_date(self, dt):
        ldate = dt
        model_qs = self.get_queryset()
        for i in xrange(0, 30):
            ldate = dt - datetime.timedelta(days=i)
            product_qs = model_qs.filter(sale_time=ldate)
            if product_qs.count() > 0:
                break
        return ldate

    def get_today_date(self):
        """ 获取今日上架日期 """
        tnow = datetime.datetime.now()
        if tnow.hour < 10:
            return self.get_latest_right_date((tnow - datetime.timedelta(days=1)).date())
        return self.get_latest_right_date(tnow.date())

    def get_previous_date(self):
        """ 获取昨日上架日期 """
        tnow = datetime.datetime.now()
        tlast = tnow - datetime.timedelta(days=1)
        if tnow.hour < 10:
            return self.get_latest_right_date((tnow - datetime.timedelta(days=2)).date())
        return self.get_latest_right_date(tlast.date())

    def get_priview_date(self, request):
        """ 获取预览上架日期 """
        tdays = int(request.GET.get('days', '0'))
        tnow = datetime.datetime.now()
        tlast = tnow + datetime.timedelta(days=tdays)
        return tlast

    def objets_from_cache(self, queryset, value_keys=['pk']):
        return list(queryset)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def previous(self, request, *args, **kwargs):
        """ 获取历史商品列表 """
        previous_dt = self.get_previous_date()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(sale_time__lt=previous_dt)

        page = self.paginate_queryset(queryset)
        if page is not None:
            object_list = self.objets_from_cache(page)
            serializer = self.get_serializer(object_list, many=True)
            return self.get_paginated_response(serializer.data)

        object_list = self.objets_from_cache(queryset)
        serializer = self.get_serializer(object_list, many=True)
        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def advance(self, request, *args, **kwargs):
        """ 获取明日商品列表 """
        advance_dt = datetime.date.today() + datetime.timedelta(days=1)
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(sale_time__gt=advance_dt)

        page = self.paginate_queryset(queryset)
        if page is not None:
            object_list = self.objets_from_cache(page)
            serializer = self.get_serializer(object_list, many=True)
            return self.get_paginated_response(serializer.data)

        object_list = self.objets_from_cache(queryset)
        serializer = self.get_serializer(object_list, many=True)
        return Response(serializer.data)

    def order_queryset(self, request, queryset, order_by=None):
        """ 对集合列表进行排序 """
        # BUGS
        order_by = order_by or request.REQUEST.get('order_by')
        if order_by == self.INDEX_ORDER_BY:
            queryset = queryset.extra(select={'is_saleout': 'remain_num - lock_num <= 0'},
                                      order_by=['-category__sort_order', 'is_saleout',
                                                '-details__is_recommend', '-details__order_weight', '-id'])
        elif order_by == 'price':
            queryset = queryset.order_by('agent_price')
        else:
            queryset = queryset.extra(select={'is_saleout': 'remain_num - lock_num <= 0'},
                                      order_by=['is_saleout', '-details__is_recommend',
                                                '-details__order_weight', '-id'])

        return queryset

    def get_custom_qs(self, queryset):
        return queryset.filter(status=Product.NORMAL, outer_id__endswith='1').exclude(details__is_seckill=True)

    def get_female_qs(self, queryset):
        return self.get_custom_qs(queryset).filter(outer_id__startswith='8')

    def get_child_qs(self, queryset):
        return self.get_custom_qs(queryset).filter(Q(outer_id__startswith='9') | Q(outer_id__startswith='1'))

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def promote_today(self, request, *args, **kwargs):
        """ 获取今日推荐商品列表 """
        today_dt = self.get_today_date()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(sale_time=today_dt, shelf_status=Product.UP_SHELF)
        queryset = self.order_queryset(request, queryset, order_by=self.INDEX_ORDER_BY)
        female_list = self.objets_from_cache(self.get_female_qs(queryset), value_keys=['pk', 'is_saleout'])
        child_list = self.objets_from_cache(self.get_child_qs(queryset), value_keys=['pk', 'is_saleout'])

        response_date = {'female_list': self.get_serializer(female_list, many=True).data,
                         'child_list': self.get_serializer(child_list, many=True).data}
        return Response(response_date)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def promote_today_paging(self, request, *args, **kwargs):
        """ 　　商品列表分页接口 """
        from django_statsd.clients import statsd
        statsd.incr('xiaolumm.home_page')
        today_dt = self.get_today_date()
        queryset = self.filter_queryset(self.get_queryset())
        tal_queryset = self.get_custom_qs(queryset).filter(
            Q(sale_time=today_dt) | Q(details__is_recommend=True),
            shelf_status=Product.UP_SHELF
        )
        queryset = self.order_queryset(request, tal_queryset, order_by=self.INDEX_ORDER_BY)
        pagin_query = self.paginate_queryset(queryset)
        if pagin_query is not None:
            object_list = self.objets_from_cache(pagin_query)
            serializer = self.get_serializer(object_list, many=True)
            return self.get_paginated_response(serializer.data)

        object_list = self.objets_from_cache(queryset, value_keys=['pk', 'is_saleout'])
        serializer = self.get_serializer(object_list, many=True)
        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def promote_previous(self, request, *args, **kwargs):
        """ 获取历史推荐商品列表 """
        previous_dt = self.get_previous_date()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(sale_time=previous_dt)
        queryset = self.order_queryset(request, queryset, order_by=self.INDEX_ORDER_BY)
        female_list = self.objets_from_cache(
            self.get_female_qs(queryset),
            value_keys=['pk', 'is_saleout']
        )
        child_list = self.objets_from_cache(
            self.get_child_qs(queryset),
            value_keys=['pk', 'is_saleout']
        )
        response_date = {'female_list': self.get_serializer(female_list, many=True).data,
                         'child_list': self.get_serializer(child_list, many=True).data}

        return Response(response_date)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def promote_previous_paging(self, request, *args, **kwargs):
        """ 昨日特卖列表分页接口 """
        previous_dt = self.get_previous_date()
        queryset = self.filter_queryset(self.get_queryset())
        tal_queryset = self.get_custom_qs(queryset).filter(
            sale_time=previous_dt
        )
        queryset = self.order_queryset(request, tal_queryset, order_by=self.INDEX_ORDER_BY)
        pagin_query = self.paginate_queryset(queryset)
        if pagin_query is not None:
            object_list = self.objets_from_cache(pagin_query)
            serializer = self.get_serializer(object_list, many=True)
            return self.get_paginated_response(serializer.data)

        object_list = self.objets_from_cache(queryset, value_keys=['pk', 'is_saleout'])
        serializer = self.get_serializer(object_list, many=True)
        return Response(serializer.data)

    @cache_response(timeout=10, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def promote_preview_paging(self, request, *args, **kwargs):
        """ 获取预览商品列表 预览页面"""
        previous_dt = self.get_priview_date(request)
        queryset = self.filter_queryset(self.get_queryset())
        queryset = self.get_custom_qs(queryset.filter(sale_time=previous_dt))
        queryset = self.order_queryset(request, queryset ,order_by=self.INDEX_ORDER_BY)
        pagin_query = self.paginate_queryset(queryset)
        if pagin_query is not None:
            object_list = self.objets_from_cache(pagin_query)
            serializer = self.get_serializer(object_list, many=True)
            return self.get_paginated_response(serializer.data)

        object_list = self.objets_from_cache(queryset, value_keys=['pk', 'is_saleout'])
        serializer = self.get_serializer(object_list, many=True)
        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def childlist(self, request, *args, **kwargs):
        """ 获取特卖童装列表 """
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(shelf_status=Product.UP_SHELF)

        child_qs = self.order_queryset(request, self.get_child_qs(queryset))
        page = self.paginate_queryset(child_qs)
        if page is not None:
            object_list = self.objets_from_cache(page)
            serializer = self.get_serializer(object_list, many=True)
            return self.get_paginated_response(serializer.data)

        object_list = self.objets_from_cache(child_qs, value_keys=['pk', 'is_saleout'])
        serializer = self.get_serializer(object_list, many=True)
        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def ladylist(self, request, *args, **kwargs):
        """ 获取特卖女装列表 """
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(shelf_status=Product.UP_SHELF)

        female_qs = self.order_queryset(request, self.get_female_qs(queryset))
        page = self.paginate_queryset(female_qs)
        if page is not None:
            object_list = self.objets_from_cache(page)
            serializer = self.get_serializer(object_list, many=True)
            return self.get_paginated_response(serializer.data)

        object_list = self.objets_from_cache(female_qs, value_keys=['pk', 'is_saleout'])
        serializer = self.get_serializer(object_list, many=True)
        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def modellist(self, request, *args, **kwargs):
        """ 获取款式商品列表 """

        model_id = kwargs.get('model_id', None)
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(model_id=model_id, status=Product.NORMAL)

        object_list = self.objets_from_cache(queryset)
        serializer = self.get_serializer(object_list, many=True)

        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def preview_modellist(self, request, *args, **kwargs):
        """ 获取款式商品列表-同款预览页面 """
        model_id = kwargs.get('model_id', None)
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(model_id=model_id, status=Product.NORMAL)

        object_list = self.objets_from_cache(queryset)
        serializer = serializers.ProductPreviewSerializer(object_list,
                                                          many=True, context={'request': request})

        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @detail_route(methods=['get'])
    def details(self, request, pk, *args, **kwargs):
        """ 商品明细，包含详细规格信息 """
        instance = self.get_object()
        product_dict = self.get_serializer(instance).data
        # 设置商品规格信息
        normal_skusdict = serializers.ProductSkuSerializer(instance.normal_skus, many=True)
        product_dict['normal_skus'] = normal_skusdict.data
        # 设置商品特卖详情
        try:
            pdetail = instance.details
            pdetail_dict = serializers.ProductdetailSerializer(pdetail).data
        except:
            pdetail_dict = {}
        product_dict['details'] = pdetail_dict

        return Response(product_dict)

    @list_route(methods=['get'])
    def seckill(self, request, *args, **kwargs):
        """
        获取秒杀商品列表
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        # 今日上架时间，shelf_status=已上架
        today_dt = self.get_today_date()
        queryset = self.filter_queryset(self.get_queryset())

        queryset = queryset.filter(details__is_seckill=True,
                                   sale_time=today_dt,
                                   shelf_status=Product.UP_SHELF)
        queryset = self.order_queryset(request, queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def verify_product(self, request, pk, *args, **kwargs):
        pro = get_object_or_404(Product, id=pk)
        if pro.is_verify:  # 如果已经审核　修改成未审核
            pro.is_verify = False
            pro.save()
            log_action(request.user.id, pro, CHANGE, u'预览时修改产品为未审核！')
        else:  # 如果未审核　修改该为已经审核
            pro.is_verify = True
            pro.save()
            log_action(request.user.id, pro, CHANGE, u'预览时修改产品为已审核！')
        res = {"is_verify": pro.is_verify, "id": pro.id}
        return Response(res)

    @list_route(methods=['get'])
    def my_choice_pro(self, request):
        """
        我的选品(不添加秒杀和卖光的产品) 这里要计算用户的佣金
        """
        content = request.REQUEST
        category = int(content.get('category', 0))  # 1童装2女装
        sort_field = content.get('sort_field', 'id')  # 排序字段

        customer = get_object_or_404(Customer, user=request.user)

        agencylevel = 1
        mama_id = 0
        try:
            xlmm = XiaoluMama.objects.get(openid=customer.unionid)
            agencylevel = xlmm.agencylevel
            mama_id = xlmm.id
        except XiaoluMama.DoesNotExist:
            pass
        # agencylevel = 2 #debug

        queryset = self.get_queryset().filter(shelf_status=Product.UP_SHELF)

        if category == 1:
            queryset = self.get_child_qs(queryset)
        elif category == 2:
            queryset = self.get_female_qs(queryset)
        else:
            queryset = self.get_custom_qs(queryset)

        extra_str = 'remain_num - lock_num > 0'
        queryset = queryset.extra(where={extra_str})  # 没有卖光的 不是秒杀产品的

        # queryset = self.paginate_queryset(queryset)

        queryset = self.choice_query_2_dict(queryset, customer, agencylevel)

        if sort_field in ['id', 'sale_num', 'rebet_amount', 'std_sale_price', 'agent_price']:
            queryset = sorted(queryset, key=lambda k: getattr(k, sort_field), reverse=True)

        queryset = self.paginate_queryset(queryset)
        serializer = serializers.ProductSimpleSerializer(queryset, many=True)
        return self.get_paginated_response(serializer.data)

    def choice_query_2_dict(self, queryset, customer, agencylevel):

        shop_products = CuShopPros.objects.filter(customer=customer.id,
                                                  pro_status=CuShopPros.UP_SHELF).values("product")
        # shop_products = CuShopPros.objects.filter(customer=19,pro_status=CuShopPros.UP_SHELF).values("product")
        product_ids = set()
        for item in shop_products:
            product_ids.add(item["product"])

        shop_product_num = len(product_ids)
        for pro in queryset:
            rebeta_scheme_id = pro.detail and pro.detail.rebeta_scheme_id or 0
            rebeta_scheme = AgencyOrderRebetaScheme.get_rebeta_scheme(rebeta_scheme_id)
            rebet_amount  = rebeta_scheme and rebeta_scheme.calculate_carry(agencylevel, pro.agent_price) or 0

            # 预留数 * 97(质数)+(97内的随机数) = (模拟)销量　
            sale_num = pro.remain_num * 19 + random.choice(xrange(19))
            pro.sale_num = sale_num

            pro.in_customer_shop = 0
            if pro.id in product_ids:
                pro.in_customer_shop = 1

            pro.shop_product_num = shop_product_num

            pro.rebet_amount = rebet_amount
            pro.sale_num_des = '{0}人在卖'.format(sale_num)
            pro.rebet_amount_des = '佣 ￥{0}.00'.format(rebet_amount)

        return queryset

    @list_route(methods=['get'])
    def get_mama_shop(self, request):
        """
        获取代理用户的店铺
        """
        content = request.REQUEST
        mm_linkid = content.get('mm_linkid', None)
        category = content.get('category', None)
        self.permission_classes = ()
        self.paginate_by = 20
        try:
            xlmm = XiaoluMama.objects.get(pk=mm_linkid)
            customer = Customer.objects.get(unionid=xlmm.openid, status=Customer.NORMAL)
            customer_id = customer.id
            shop = CustomerShops.objects.get(customer=customer_id)
            shop_info = model_to_dict(shop, fields=['name'])
            shop_info['thumbnail'] = customer.thumbnail or 'http://7xogkj.com2.z0.glb.qiniucdn.com/1181123466.jpg'
            shop_pros = CuShopPros.objects.filter(shop=shop.id, pro_status=CuShopPros.UP_SHELF).order_by('-position')
            if shop_pros.count() == 0:  # 如果用户店铺没有上架商品则初始化添加推荐商品
                from flashsale.pay.tasks import task_add_product_to_customer_shop
                task_add_product_to_customer_shop(customer)
        except:
            return Response({"shop_info": None, "products": None})
        from flashsale.pay.constants import FEMALE_CID_LIST, CHILD_CID_LIST
        if category == 'child':
            queryset = shop_pros.filter(pro_category__in=CHILD_CID_LIST)
        elif category == 'female':
            queryset = shop_pros.filter(pro_category__in=FEMALE_CID_LIST)
        else:
            queryset = shop_pros
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = serializers.CuShopProsSerialize(page, many=True)
            return self.get_paginated_response({"shop_info": shop_info, "products": serializer.data})
        serializer = serializers.CuShopProsSerialize(queryset, many=True)
        return Response({"shop_info": shop_info, "products": serializer.data})

    @list_route(methods=['get'])
    @cache_response(timeout=30, key_func='calc_items_cache_key')
    def promotion_ads(self, request, *args, **kwargs):
        """ 推荐展示商品信息 """
        content = request.REQUEST
        category = content.get('category')
        list_num = int(content.get('lnum', '1'))

        product_list = []
        dress_pids = DressProduct.filter_by_many(**content)
        dress_products = self.get_queryset().filter(id__in=dress_pids, shelf_status=Product.UP_SHELF)
        for product in dress_products:
            product_list.append(product)

        delta_num = list_num - len(product_list)
        if delta_num > 0:
            product_qs = self.get_queryset().filter(shelf_status=Product.UP_SHELF)
            product_qs = self.order_queryset(request, product_qs)

            if category and category.isdigit():
                product_qs = product_qs.filter(category=category)

            product_list.extend(product_qs[0:delta_num])

        serializer = serializers.SimpleProductSerializer(product_list, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def brandlist(self, request, *args, **kwargs):
        """ 品牌推广展示商品信息 """
        content = request.REQUEST
        brand_id = content.get('brand')

        tnow = datetime.datetime.now()
        queryset = BrandProduct.objects.filter(brand_id=brand_id)
        resultset = Product.objects.none()
        for brand in queryset:
            resultset = resultset | (Product.objects.filter(id=brand.product_id))
        pagin_query = self.paginate_queryset(resultset)
        if pagin_query is not None:
            object_list = self.objets_from_cache(pagin_query)
            serializer = self.get_serializer(object_list, many=True)
            return self.get_paginated_response(serializer.data)

        object_list = self.objets_from_cache(queryset, value_keys=['pk', 'is_saleout'])
        serializer = self.get_serializer(object_list, many=True)
        return Response(serializer.data)


class ProductShareView(generics.RetrieveAPIView):
    """ 获取特卖商品快照 """
    queryset = Product.objects.all()  # ,shelf_status=Product.UP_SHELF
    serializer_class = serializers.ProductSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer, renderers.TemplateHTMLRenderer)
    template_name = 'shangpin_share.html'
    QR_IMG_PATH = 'qrcode/product/'

    def get_share_link(self, params):
        link = urlparse.urljoin(settings.M_SITE_URL, 'pages/shangpinxq.html?id={product_id}&mm_linkid={linkid}')
        return link.format(**params)

    def get_xlmm(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        if not customer.unionid.strip():
            return None
        xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
        return xiaolumms.count() > 0 and xiaolumms[0] or None

    def gen_item_share_qrcode_link(self, product_id, linkid=None):

        params = {'product_id': product_id, 'linkid': linkid}
        file_name = os.path.join(self.QR_IMG_PATH, 'qr-{linkid}-{product_id}.jpg'.format(**params))

        share_link = self.get_share_link(params)

        from core.upload.xqrcode import push_qrcode_to_remote
        qrlink = push_qrcode_to_remote(file_name, share_link)

        return qrlink

    def get(self, request, format=None, *args, **kwargs):

        instance = self.get_object()
        product_dict = self.get_serializer(instance).data
        # 设置商品规格信息
        normal_skusdict = serializers.ProductSkuSerializer(instance.normal_skus, many=True)
        product_dict['normal_skus'] = normal_skusdict.data
        # 设置商品特卖详情
        try:
            pdetail = instance.details
            pdetail_dict = serializers.ProductdetailSerializer(pdetail).data
        except:
            pdetail_dict = {}
        product_dict['details'] = pdetail_dict
        if format == 'html':
            product_dict['M_STATIC_URL'] = settings.M_STATIC_URL

        xlmm = self.get_xlmm(request)
        product_dict['share_qrcode'] = self.gen_item_share_qrcode_link(instance.id, linkid=xlmm and xlmm.id or 0)

        return Response(product_dict)



