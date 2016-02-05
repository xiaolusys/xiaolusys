# -*- coding:utf-8 -*-
import os
import json
import datetime
import hashlib
import urlparse
from django.conf import settings
from django.shortcuts import get_object_or_404, render_to_response
from django.db.models import Q

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

from shopback.items.models import Product
from shopback.categorys.models import ProductCategory
from flashsale.pay.models import GoodShelf,ModelProduct
from flashsale.pay.models_custom import Productdetail
from flashsale.pay.models import Customer
from flashsale.xiaolumm.models import XiaoluMama

from . import permissions as perms
from . import serializers
from .options import gen_and_save_jpeg_pic
from shopback.base import log_action, ADDITION, CHANGE
from django.forms import model_to_dict
from flashsale.xiaolumm.models_rebeta import AgencyOrderRebetaScheme

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
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)

    def calc_porter_cache_key(self, view_instance, view_method,
                            request, args, kwargs):
        key_vals = ['days']
        key_maps = kwargs or {}
        for k,v in request.GET.copy().iteritems():
            if k in key_vals and v.strip():
                key_maps[k] = v
        
        return hashlib.sha1(u'.'.join([
                view_instance.__module__,
                view_instance.__class__.__name__,
                view_method.__name__,
                json.dumps(key_maps, sort_keys=True).encode('utf-8')
            ])).hexdigest()
    
    def get_latest_right_date(self,dt):
        ldate = dt
        model_qs = self.get_queryset()
        for i in xrange(0,30):
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

    def get_future_poster(self,request):
        view_days   = int(request.GET.get('days','1'))
        target_date = datetime.date.today() + datetime.timedelta(days=view_days)
        target_date = self.get_latest_right_date(target_date)
        posters = self.queryset.filter(active_time__year=target_date.year,
                                   active_time__month=target_date.month,
                                   active_time__day=target_date.day)
        return posters.count() and posters[0] or None
    
    def list(self, request, *args, **kwargs):
        raise exceptions.APIException(u'该接口暂未提供数据')
    
    @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_porter_cache_key')
    @list_route(methods=['get'])
    def today(self, request, *args, **kwargs):
        poster = self.get_today_poster()
        serializer = self.get_serializer(poster, many=False)
        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_porter_cache_key')
    @list_route(methods=['get'])
    def previous(self, request, *args, **kwargs):
        poster = self.get_previous_poster()
        serializer = self.get_serializer(poster, many=False)
        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_porter_cache_key')
    @list_route(methods=['get'])
    def preview(self, request, *args, **kwargs):
        poster = self.get_future_poster(request)
        serializer = self.get_serializer(poster, many=False)
        return Response(serializer.data)

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ##特卖商品API：
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
    """
    queryset = Product.objects.all()
    serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer)

    paginate_by = 100
    page_query_param = 'page'
    paginate_by_param = 'page_size'
    max_paginate_by = 100
    INDEX_ORDER_BY = 'main'

    def calc_items_cache_key(self, view_instance, view_method,
                            request, args, kwargs):
        key_vals = ['order_by','id','model_id','days','page','page_size']
        key_maps = kwargs or {}
        for k,v in request.GET.copy().iteritems():
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
    
    def get_latest_right_date(self,dt):
        ldate = dt
        model_qs = self.get_queryset().filter(shelf_status=Product.UP_SHELF)
        for i in xrange(0,30):
            ldate = dt - datetime.timedelta(days=i)
            product_qs = model_qs.filter(sale_time=ldate)
            if product_qs.count() > 0:
                break
        return ldate
    
    def get_preview_right_date(self,dt):
        ldate = dt
        model_qs = self.get_queryset()
        for i in xrange(0,30):
            ldate = dt - datetime.timedelta(days=i)
            product_qs = model_qs.filter(sale_time=ldate)
            if product_qs.count() > 0:
                break
        return ldate

    def get_today_date(self):
        """ 获取今日上架日期 """
        tnow  = datetime.datetime.now()
        if tnow.hour < 10:
            return self.get_latest_right_date((tnow - datetime.timedelta(days=1)).date())
        return self.get_latest_right_date(tnow.date())

    def get_previous_date(self):
        """ 获取昨日上架日期 """
        tnow  = datetime.datetime.now()
        tlast = tnow - datetime.timedelta(days=1)
        if tnow.hour < 10:
            return self.get_latest_right_date((tnow - datetime.timedelta(days=2)).date())
        return self.get_latest_right_date(tlast.date())

    def get_priview_date(self,request):
        """ 获取明日上架日期 """
        tdays  = int(request.GET.get('days','0'))
        tnow   = datetime.datetime.now()
        tlast  = tnow + datetime.timedelta(days=tdays)
        return self.get_preview_right_date(tlast.date())
    
    def objets_from_cache(self,queryset,value_keys=['pk']):
        if type(queryset) is list:
            return queryset
        if len(value_keys) == 1:
            lookup_pks = queryset.values_list(*value_keys, flat=True)
        else:
            lookup_pks = [v[0] for v in queryset.values_list(*value_keys)]
        return Product.objects.from_ids(lookup_pks)
        
    
    @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_items_cache_key')
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

    @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_items_cache_key')
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

    def order_queryset(self,request,queryset,order_by=None):
        """ 对集合列表进行排序 """
        #BUGS
        order_by = order_by or request.REQUEST.get('order_by')
        if order_by == self.INDEX_ORDER_BY:
            queryset = queryset.extra(select={'is_saleout':'remain_num - lock_num <= 0'},
                                      order_by=['-category__sort_order','is_saleout', 
                                                '-details__is_recommend','-details__order_weight','-id'])
        elif order_by == 'price':
            queryset = queryset.order_by('agent_price')
        else:
            queryset = queryset.extra(select={'is_saleout':'remain_num - lock_num <= 0'},
                                      order_by=['is_saleout','-details__is_recommend',
                                                '-details__order_weight','-id'])
        
        return queryset

    def get_custom_qs(self,queryset):
        return queryset.filter(status=Product.NORMAL,outer_id__endswith='1')#.exclude(details__is_seckill=True)

    def get_female_qs(self,queryset):
        return self.get_custom_qs(queryset).filter(outer_id__startswith='8')

    def get_child_qs(self,queryset):
        return self.get_custom_qs(queryset).filter(Q(outer_id__startswith='9')|Q(outer_id__startswith='1'))

    @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def promote_today(self, request, *args, **kwargs):
        """ 获取今日推荐商品列表 """
        today_dt = self.get_today_date()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(sale_time=today_dt,shelf_status=Product.UP_SHELF)
        queryset = self.order_queryset(request, queryset, order_by=self.INDEX_ORDER_BY)
        female_list = self.objets_from_cache(self.get_female_qs(queryset),value_keys=['pk','is_saleout'])
        child_list  = self.objets_from_cache(self.get_child_qs(queryset),value_keys=['pk','is_saleout'])
        
        response_date = {'female_list':self.get_serializer(female_list, many=True).data,
                         'child_list':self.get_serializer(child_list, many=True).data}
        return Response(response_date)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT, key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def promote_today_paging(self, request, *args, **kwargs):
        """ 　　商品列表分页接口 """
        today_dt = self.get_today_date()
        queryset = self.filter_queryset(self.get_queryset())
        tal_queryset = self.get_custom_qs(queryset).filter(
            Q(sale_time=today_dt)|Q(details__is_recommend=True),
            shelf_status=Product.UP_SHELF
        )
        queryset = self.order_queryset(request, tal_queryset, order_by=self.INDEX_ORDER_BY)
        pagin_query = self.paginate_queryset(queryset)
        if pagin_query is not None:
            object_list = self.objets_from_cache(pagin_query)
            serializer = self.get_serializer(object_list, many=True)
            return self.get_paginated_response(serializer.data)
        
        object_list = self.objets_from_cache(queryset, value_keys=['pk','is_saleout'])
        serializer = self.get_serializer(object_list, many=True)
        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def promote_previous(self, request, *args, **kwargs):
        """ 获取历史推荐商品列表 """
        previous_dt = self.get_previous_date()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(sale_time=previous_dt)
        queryset = self.order_queryset(request, queryset, order_by=self.INDEX_ORDER_BY)
        female_list = self.objets_from_cache(
            self.get_female_qs(queryset),
            value_keys=['pk','is_saleout']
        )
        child_list  = self.objets_from_cache(
            self.get_child_qs(queryset), 
            value_keys=['pk','is_saleout']
        )
        response_date = {'female_list':self.get_serializer(female_list, many=True).data,
                         'child_list':self.get_serializer(child_list, many=True).data}

        return Response(response_date)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_items_cache_key')
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
        
        object_list = self.objets_from_cache(queryset, value_keys=['pk','is_saleout'])
        serializer = self.get_serializer(object_list, many=True)
        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def promote_preview(self, request, *args, **kwargs):
        """ 获取历史推荐商品列表 预览页面"""
        previous_dt = self.get_priview_date(request)
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(sale_time=previous_dt)
        queryset = self.order_queryset(request, queryset)
        female_list = self.objets_from_cache(
            self.get_female_qs(queryset),
            value_keys=['pk','is_saleout']
        )
        child_list  = self.objets_from_cache(
            self.get_child_qs(queryset),
            value_keys=['pk','is_saleout']
        )

        response_date = {
            'female_list': serializers.ProductPreviewSerializer(
                 female_list, 
                 many=True,
                 context={'request': request}).data,
            'child_list': serializers.ProductPreviewSerializer(
                 child_list, 
                 many=True,
                 context={'request': request}).data}
        return Response(response_date)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_items_cache_key')
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
        
        object_list = self.objets_from_cache(child_qs,value_keys=['pk','is_saleout'])
        serializer = self.get_serializer(object_list, many=True)
        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def ladylist(self, request, *args, **kwargs):
        """ 获取特卖女装列表 """
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(shelf_status=Product.UP_SHELF)

        female_qs = self.order_queryset(request,self.get_female_qs(queryset))
        page = self.paginate_queryset(female_qs)
        if page is not None:
            object_list = self.objets_from_cache(page)
            serializer = self.get_serializer(object_list, many=True)
            return self.get_paginated_response(serializer.data)
        
        object_list = self.objets_from_cache(female_qs,value_keys=['pk','is_saleout'])
        serializer = self.get_serializer(object_list, many=True)
        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_items_cache_key')
    @list_route(methods=['get'])
    def modellist(self, request, *args, **kwargs):
        """ 获取款式商品列表 """

        model_id = kwargs.get('model_id',None)
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(model_id=model_id, status=Product.NORMAL)
        
        object_list = self.objets_from_cache(queryset)
        serializer = self.get_serializer(object_list, many=True)

        return Response(serializer.data)

    @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_items_cache_key')
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

    @cache_response(timeout=CACHE_VIEW_TIMEOUT,key_func='calc_items_cache_key')
    @detail_route(methods=['get'])
    def details(self, request, pk, *args, **kwargs):
        """ 商品明细，包含详细规格信息 """
        instance = self.get_object()
        product_dict = self.get_serializer(instance).data
        #设置商品规格信息
        normal_skusdict = serializers.ProductSkuSerializer(instance.normal_skus,many=True)
        product_dict['normal_skus'] = normal_skusdict.data
        #设置商品特卖详情
        try:
            pdetail = instance.details
            pdetail_dict = serializers.ProductdetailSerializer(pdetail).data
        except:
            pdetail_dict  = {}
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
        customer = get_object_or_404(Customer, user=request.user)
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(shelf_status=Product.UP_SHELF)

        queryset = self.get_child_qs(queryset) if category == 1 else queryset
        queryset = self.get_female_qs(queryset) if category == 2 else queryset

        extra_str = 'remain_num - lock_num > 0 AND NOT name REGEXP "^秒杀"'
        queryset = queryset.extra(where={extra_str})  # 没有卖光的 不是秒杀产品的
        pros = self.choice_query_2_dict(queryset, customer, request)
        return Response(pros)

    def choice_query_2_dict(self, queryset, customer, request):
        pros = []
        rebt = AgencyOrderRebetaScheme.objects.get(id=1)
        content = request.REQUEST
        sort_field = content.get('sort_field', 'id')  # 排序字段
        try:
            xlmm = XiaoluMama.objects.get(openid=customer.unionid)
        except XiaoluMama.DoesNotExist:
            xlmm = False
        model_ids = []
        for pro in queryset:
            if pro.model_id in model_ids:
                continue
            kwargs = {'agencylevel': xlmm.agencylevel,
                      'payment': float(pro.agent_price)} if xlmm and pro.agent_price else {}
            rebet_amount = rebt.get_scheme_rebeta(**kwargs) if kwargs else 0  # 计算佣金
            prodic = model_to_dict(pro, fields=['id', 'pic_path', 'name', 'std_sale_price', 'agent_price', 'lock_num'])
            prodic['in_customer_shop'] = pro.in_customer_shop(customer.id)
            prodic['rebet_amount'] = rebet_amount
            pros.append(prodic)
            model_ids.append(pro.model_id)
        if sort_field:
            pros = sorted(pros, key=lambda k: k[sort_field], reverse=True)
        return pros


class ProductShareView(generics.RetrieveAPIView):
    """ 获取特卖商品快照 """
    queryset = Product.objects.filter()#,shelf_status=Product.UP_SHELF
    serializer_class = serializers.ProductSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,renderers.TemplateHTMLRenderer)
    template_name = 'shangpin_share.html'
    QR_IMG_PATH    = 'qr'

    def get_share_link(self,params):
        link = urlparse.urljoin(settings.M_SITE_URL,'pages/shangpinxq.html?id={product_id}&mm_linkid={linkid}')
        return link.format(**params)

    def get_xlmm(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        if not customer.unionid.strip():
            return None
        xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
        return xiaolumms.count() > 0 and xiaolumms[0] or None

    def gen_item_share_qrcode_link(self, product_id, linkid=None):

        root_path = os.path.join(settings.MEDIA_ROOT,self.QR_IMG_PATH)
        if not os.path.exists(root_path):
            os.makedirs(root_path)

        params = {'product_id':product_id, 'linkid':linkid}
        file_name = 'qr-{linkid}-{product_id}.jpg'.format(**params)
        file_path = os.path.join(root_path,file_name)

        share_link = self.get_share_link(params)
        if not os.path.exists(file_path):
            gen_and_save_jpeg_pic(share_link,file_path)

        return os.path.join(settings.MEDIA_URL,self.QR_IMG_PATH,file_name)

    def get(self, request, format=None,*args, **kwargs):

        instance = self.get_object()
        product_dict = self.get_serializer(instance).data
        #设置商品规格信息
        normal_skusdict = serializers.ProductSkuSerializer(instance.normal_skus,many=True)
        product_dict['normal_skus'] = normal_skusdict.data
        #设置商品特卖详情
        try:
            pdetail = instance.details
            pdetail_dict = serializers.ProductdetailSerializer(pdetail).data
        except:
            pdetail_dict  = {}
        product_dict['details'] = pdetail_dict
        if format == 'html':
            product_dict['M_STATIC_URL'] = settings.M_STATIC_URL

        xlmm = self.get_xlmm(request)
        product_dict['share_qrcode'] = self.gen_item_share_qrcode_link(instance.id,linkid=xlmm and xlmm.id or 0)

        return Response(product_dict)
