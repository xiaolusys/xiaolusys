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
from rest_framework.response import Response
from rest_framework import exceptions
from rest_framework_extensions.cache.decorators import cache_response

from shopback.items.models import Product
from flashsale.pay.models import (
    GoodShelf,
    ModelProduct,
    Productdetail,
    BrandProduct,
    CustomerShops,
    CuShopPros,
    Customer
)
from flashsale.promotion.models import ActivityEntry
from flashsale.xiaolumm.models import XiaoluMama, MamaTabVisitStats
from flashsale.mmexam.models import DressProduct

from flashsale.restpro.v1 import serializers
from flashsale.restpro.v2 import serializers as serializersv2

from shopback.items import constants as itemcons

CACHE_VIEW_TIMEOUT = 30

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ##特卖商品API：
    > ### [.format]: 获取今日推荐商品列表;
      - `page`:页码（０开始）
      - `page_size`：每页数量初始为10
    > ### /yesterday[.format]: 获取昨日推荐商品列表;
    > ### /tomorrow：获取明日推荐商品列表;
    > ### /childlist[.format]: 获取童装专区商品列表;
    > ### /ladylist[.format]: 获取女装专区商品列表;
    > ### /modellist/{model_id}[.format]:获取聚合商品列表;
      - model_id:款式ID
    > ### /{pk}/details[.format]: 商品详情;
    > ### /{pk}/snapshot.html: 获取特卖商品快照（需登录）;
    > ### /my_choice_pro: 获取'我的选品列表'产品数据
      - params: category=[1,2]
      - sort_field= ['id', 'sale_num', 'rebet_amount', 'std_sale_price', 'agent_price']
      - page=n (n >= 1)
      - page_size=n (n >= 1)
    """
    # TODO@CAUTION this class has been replaced by ModelProductViewSet
    queryset = Product.objects.all()
    serializer_class = serializers.SimpleProductSerializer
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

    def get_latest_right_date(self, dt):
        ldate = dt
        model_qs = self.get_queryset().filter(status=Product.NORMAL)
        for i in xrange(0, 30):
            ldate = dt - datetime.timedelta(days=i)
            product_qs = model_qs.filter(sale_time=ldate)
            if product_qs.exists():
                break
        return ldate

    def get_preview_right_date(self, dt):
        ldate = dt
        model_qs = self.get_queryset().filter(status=Product.NORMAL)
        for i in xrange(0, 30):
            ldate = dt + datetime.timedelta(days=i)
            product_qs = model_qs.filter(sale_time=ldate)
            if product_qs.exists():
                break
        return ldate

    def get_today_date(self):
        """ 获取今日上架日期 """
        tnow = datetime.datetime.now()
        if tnow.hour < 10:
            return self.get_latest_right_date((tnow - datetime.timedelta(days=1)).date())
        return self.get_latest_right_date(tnow.date())

    def get_yesterday_date(self):
        """ 获取昨日上架日期 """
        tnow = datetime.datetime.now()
        tlast = tnow - datetime.timedelta(days=1)
        if tnow.hour < 10:
            return self.get_latest_right_date((tnow - datetime.timedelta(days=2)).date())
        return self.get_latest_right_date(tlast.date())

    def get_tomorrow_date(self):
        """ 获取昨日上架日期 """
        tnow = datetime.datetime.now()
        tlast = tnow + datetime.timedelta(days=1)
        if tnow.hour < 10:
            return self.get_preview_right_date(tnow.date())
        return self.get_preview_right_date(tlast.date())

    def get_priview_date(self, request):
        """ 获取明日上架日期 """
        tdays = int(request.GET.get('days', '0'))
        tnow = datetime.datetime.now()
        tlast = tnow + datetime.timedelta(days=tdays)
        return self.get_preview_right_date(tlast.date())

    def objets_from_cache(self, queryset, value_keys=['pk']):
        return list(queryset)

    def order_queryset(self, request, queryset, order_by=None):
        """ 对集合列表进行排序 """
        order_by = order_by or request.GET.get('order_by')
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
        return queryset.filter(status=Product.NORMAL, outer_id__endswith=itemcons.MALL_PRODUCT_ENDCODE).exclude(details__is_sale=True)

    def get_female_qs(self, queryset):
        return self.get_custom_qs(queryset).filter(outer_id__startswith=itemcons.MALL_FEMALE_STARTCODE)

    def get_child_qs(self, queryset):
        return self.get_custom_qs(queryset).filter(Q(outer_id__startswith=itemcons.MALL_CHILD_STARTCODE)
                                                   | Q(outer_id__startswith=itemcons.MALL_PARENT_STARTCODE))

    def get_downshelf_deadline(self, obj_list, cur_date):
        deadline = datetime.datetime.combine(cur_date, datetime.datetime.min.time())\
                    + datetime.timedelta(seconds= 38 * 60 * 60)
        for obj in obj_list:
            if obj.offshelf_time and obj.offshelf_time > deadline:
                deadline = obj.offshelf_time
        return deadline

    def get_pagination_response_by_date(self, request, cur_date, only_upshelf=True):
        today = datetime.date.today()
        queryset = self.filter_queryset(self.get_queryset())
        tal_queryset = self.get_custom_qs(queryset)
        if only_upshelf:
            tal_queryset = tal_queryset.filter(
                Q(sale_time=cur_date) | Q(details__is_recommend=True),
                shelf_status=Product.UP_SHELF
            )
        else:
            tal_queryset = tal_queryset.filter(
                sale_time=cur_date
            )
        queryset = self.order_queryset(request, tal_queryset, order_by=self.INDEX_ORDER_BY)
        pagin_query = self.paginate_queryset(queryset)
        if pagin_query is not None:
            object_list = self.objets_from_cache(pagin_query)
            serializer = self.get_serializer(object_list, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data.update({
                'downshelf_deadline': self.get_downshelf_deadline(object_list, cur_date).strftime("%Y-%m-%d %H:%M:%S"),
                'upshelf_starttime': (datetime.datetime.combine(cur_date, datetime.datetime.min.time())\
                                + datetime.timedelta(seconds= 10 * 60 * 60)).strftime("%Y-%m-%d %H:%M:%S")
            })
            return response

        object_list = self.objets_from_cache(queryset, value_keys=['pk', 'is_saleout'])
        serializer  = self.get_serializer(object_list, many=True)

        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    def list(self, request, *args, **kwargs):
        """ 今日商品列表分页接口 """
        from django_statsd.clients import statsd
        statsd.incr('xiaolumm.home_page')
        today_dt = self.get_today_date()
        return self.get_pagination_response_by_date(request, today_dt, only_upshelf=True)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def yesterday(self, request, *args, **kwargs):
        """ 昨日特卖列表分页接口 """
        yesterday_dt = self.get_yesterday_date()
        return self.get_pagination_response_by_date(request, yesterday_dt, only_upshelf=False)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def tomorrow(self, request, *args, **kwargs):
        """ 昨日特卖列表分页接口 """
        tomorrow_dt = self.get_tomorrow_date()
        return self.get_pagination_response_by_date(request, tomorrow_dt, only_upshelf=False)

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
    @detail_route(methods=['get'])
    def details(self, request, pk, *args, **kwargs):
        """ 商品明细，包含详细规格信息 """
        instance = self.get_object()
        product_dict = serializers.ProductSerializer(instance).data
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
    def my_choice_pro(self, request):
        """
        我的选品(不添加秒杀和卖光的产品) 这里要计算用户的佣金
        """
        content = request.GET
        category = int(content.get('category', 0))  # 1童装2女装
        sort_field = content.get('sort_field', 'id')  # 排序字段
        if not request.user.is_authenticated():
            raise exceptions.APIException(u'请登录后访问')
        customer = get_object_or_404(Customer, user=request.user)
        queryset = self.get_queryset().filter(shelf_status=Product.UP_SHELF,
                                              status=Product.NORMAL, outer_id__endswith='1')
        if category == 1:
            queryset = queryset.filter(outer_id__startswith=itemcons.MALL_CHILD_STARTCODE)
        elif category == 2:
            queryset = queryset.filter(outer_id__startswith=itemcons.MALL_FEMALE_STARTCODE)
        else:
            queryset = queryset

        extra_str = 'remain_num - lock_num > 0'
        queryset = queryset.extra(where={extra_str})  # 没有卖光的 不是秒杀产品的

        product_ids = CuShopPros.objects.filter(customer=customer.id,
                                                  pro_status=CuShopPros.UP_SHELF).values_list("product",flat=True)
        product_ids = set(product_ids)
        shop_product_num = len(product_ids)
        xlmm = customer.get_charged_mama()

        visit_tab = MamaTabVisitStats.TAB_CARRY_LIST
        from flashsale.xiaolumm.tasks import task_mama_daily_tab_visit_stats
        task_mama_daily_tab_visit_stats.delay(xlmm.id, visit_tab)

        from flashsale.xiaolumm.models.models_rebeta import AgencyOrderRebetaScheme
        next_agentinfo = xlmm.next_agencylevel_info()
        for pro in queryset:
            pro.in_customer_shop = 1 if pro.id in product_ids else 0
            rebeta_scheme_id = pro.detail and pro.detail.rebeta_scheme_id or 0
            rebate_scheme = AgencyOrderRebetaScheme.get_rebeta_scheme(rebeta_scheme_id)
            rebet_amount = rebate_scheme.calculate_carry(xlmm.agencylevel, pro.agent_price)
            pro.rebet_amount = round(rebet_amount, 2)
            pro.rebet_amount_des = u'佣 ￥{0}'.format(pro.rebet_amount)

            next_rebet_amount = rebate_scheme and rebate_scheme.calculate_carry(
                next_agentinfo[0], pro.agent_price) or 0
            pro.next_rebet_amount = round(next_rebet_amount, 2)
            pro.next_rebet_amount_des = u'佣 ￥{0}'.format(pro.next_rebet_amount)

        if sort_field in ['id', 'sale_num', 'rebet_amount', 'std_sale_price', 'agent_price']:
            queryset = sorted(queryset, key=lambda k: getattr(k, sort_field), reverse=True)

        queryset = self.paginate_queryset(queryset)
        serializer = serializersv2.ProductSimpleSerializerV2(queryset, many=True,
                                                             context={'request': request,
                                                                      'xlmm': xlmm,
                                                                      "shop_product_num": shop_product_num})
        return self.get_paginated_response(serializer.data)

    @list_route(methods=['get'])
    def get_mama_shop(self, request):
        """
        获取代理用户的店铺
        """
        content = request.GET
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
        content = request.GET
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
        content = request.GET
        brand_id = content.get('brand')

        tnow = datetime.datetime.now()
        queryset = BrandProduct.objects.filter(brand_id=brand_id)
        resultset = Product.objects.none()
        for brand in queryset:
            print "product id %d"%brand.product_id
            resultset = resultset | (Product.objects.filter(id=brand.product_id))
        print resultset.count()
        pagin_query = self.paginate_queryset(resultset)
        if pagin_query is not None:
            object_list = self.objets_from_cache(pagin_query)
            serializer = self.get_serializer(object_list, many=True)
            return self.get_paginated_response(serializer.data)

        object_list = self.objets_from_cache(queryset, value_keys=['pk', 'is_saleout'])
        serializer = self.get_serializer(object_list, many=True)
        return Response(serializer.data)
