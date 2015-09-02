# -*- coding:utf8 -*-
import datetime
from django.shortcuts import get_object_or_404
from django.db.models import Q

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status

from shopback.items.models import Product
from shopback.categorys.models import ProductCategory
from flashsale.pay.models import GoodShelf,ModelProduct
from flashsale.pay.models_custom import Productdetail

from . import permissions as perms
from . import serializers 


class PosterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    特卖海报API：
    - {prefix}/today[.format]: 获取今日特卖海报;
    - {prefix}/previous[.format]: 获取昨日特卖海报;
    """
    queryset = GoodShelf.objects.filter(is_active=True)
    serializer_class = serializers.PosterSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    def get_today_poster(self):
        target_date = datetime.date.today()
        posters = self.queryset.filter(active_time__year=target_date.year,
                                    active_time__month=target_date.month,
                                    active_time__day=target_date.day)
        return posters.count() and posters[0] or None
    
    def get_previous_poster(self):
        target_date = datetime.date.today() - datetime.timedelta(days=1)
        posters = self.queryset.filter(active_time__year=target_date.year,
                                   active_time__month=target_date.month,
                                   active_time__day=target_date.day)
        return posters.count() and posters[0] or None
    
    def get_future_poster(self,request):
        view_days   = int(request.GET.get('days','1'))
        target_date = datetime.date.today() + datetime.timedelta(days=view_days)
        print target_date
        posters = self.queryset.filter(active_time__year=target_date.year,
                                   active_time__month=target_date.month,
                                   active_time__day=target_date.day)
        return posters.count() and posters[0] or None
    
    @list_route(methods=['get'])
    def today(self, request, *args, **kwargs):
        poster = self.get_today_poster()
        serializer = self.get_serializer(poster, many=False)
        return Response(serializer.data)
    
    @list_route(methods=['get'])
    def previous(self, request, *args, **kwargs):
        poster = self.get_previous_poster()
        serializer = self.get_serializer(poster, many=False)
        return Response(serializer.data)
    
    @list_route(methods=['get'])
    def preview(self, request, *args, **kwargs):
        poster = self.get_future_poster(request)
        serializer = self.get_serializer(poster, many=False)
        return Response(serializer.data)

from rest_framework_extensions.cache.decorators import cache_response

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    特卖商品API：
    
    - {prefix}/promote_today[.format]: 获取今日推荐商品列表;
    - {prefix}/promote_previous[.format]: 获取昨日推荐商品列表;
    - {prefix}/childlist[.format]: 获取童装专区商品列表;
    - {prefix}/ladylist[.format]: 获取女装专区商品列表;
    - {prefix}/previous[.format]: 获取昨日特卖商品列表;
    - {prefix}/advance[.format]: 获取明日特卖商品列表;
    - {prefix}/seckill[.format]: 获取秒杀商品列表;
    - {prefix}/modellist/{model_id}[.format]:获取聚合商品列表（model_id:款式ID）
    """
    queryset = Product.objects.filter(status=Product.NORMAL)#,shelf_status=Product.UP_SHELF
    serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    paginate_by = 70
    page_query_param = 'page_size'
    max_paginate_by = 100
    
    def get_today_date(self):
        """ 获取今日上架日期 """
        tnow  = datetime.datetime.now()
        if tnow.hour < 10:
            return (tnow - datetime.timedelta(days=1)).date()
        return tnow.date()
    
    def get_previous_date(self):
        """ 获取昨日上架日期 """
        tnow  = datetime.datetime.now()
        tlast = tnow - datetime.timedelta(days=1)
        if tnow.hour < 10:
            return (tnow - datetime.timedelta(days=2)).date()
        return tlast.date()
    
    def get_priview_date(self,request):
        """ 获取明日上架日期 """
        tdays  = int(request.GET.get('days','1'))
        tnow   = datetime.datetime.now() 
        tlast  = tnow + datetime.timedelta(days=tdays)
        return tlast.date()
    
    @cache_response()
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @cache_response()
    @list_route(methods=['get'])
    def previous(self, request, *args, **kwargs):
        """ 获取历史商品列表 """
        previous_dt = self.get_previous_date()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(sale_time__lt=previous_dt)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
 
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @cache_response()
    @list_route(methods=['get'])
    def advance(self, request, *args, **kwargs):
        """ 获取明日商品列表 """
        advance_dt = datetime.date.today() + datetime.timedelta(days=1)
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(sale_time__gt=advance_dt)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def order_queryset(self,request,queryset):
        """ 对集合列表进行排序 """
        order_by = request.REQUEST.get('order_by')
        if order_by == 'price':
            queryset = queryset.order_by('agent_price')
        else:
            queryset = queryset.order_by('-wait_post_num')
        return queryset
    
    def get_female_qs(self,queryset):
        return queryset.filter(outer_id__startswith='8',outer_id__endswith='1',details__is_seckill=False)
    
    def get_child_qs(self,queryset):
        return queryset.filter(Q(outer_id__startswith='9')|Q(outer_id__startswith='1'),outer_id__endswith='1',details__is_seckill=False)
    
    @cache_response()
    @list_route(methods=['get'])
    def promote_today(self, request, *args, **kwargs):
        """ 获取今日推荐商品列表 """
        today_dt = self.get_today_date()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(sale_time=today_dt).order_by('-wait_post_num')
        import time
        print 'debug promote:',time.time()
        female_qs = self.get_female_qs(queryset)
        child_qs  = self.get_child_qs(queryset)
        
        response_date = {'female_list':self.get_serializer(female_qs, many=True).data,
                         'child_list':self.get_serializer(child_qs, many=True).data}
        
        return Response(response_date)
    
    @cache_response()
    @list_route(methods=['get'])
    def promote_previous(self, request, *args, **kwargs):
        """ 获取历史推荐商品列表 """
        previous_dt = self.get_previous_date()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(sale_time=previous_dt).order_by('-wait_post_num')
        
        female_qs = self.get_female_qs(queryset)
        child_qs  = self.get_child_qs(queryset)
        
        response_date = {'female_list':self.get_serializer(female_qs, many=True).data,
                         'child_list':self.get_serializer(child_qs, many=True).data}
        
        return Response(response_date)
    
    @list_route(methods=['get'])
    def promote_preview(self, request, *args, **kwargs):
        """ 获取历史推荐商品列表 """
        previous_dt = self.get_priview_date(request)
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(sale_time=previous_dt).order_by('-wait_post_num')
        
        female_qs = self.get_female_qs(queryset)
        child_qs  = self.get_child_qs(queryset)
        
        response_date = {'female_list':self.get_serializer(female_qs, many=True).data,
                         'child_list':self.get_serializer(child_qs, many=True).data}
        
        return Response(response_date)
    
    @cache_response()
    @list_route(methods=['get'])
    def childlist(self, request, *args, **kwargs):
        """ 获取特卖童装列表 """
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(shelf_status=Product.UP_SHELF)
   
        child_qs = self.order_queryset(request, self.get_child_qs(queryset))
        page = self.paginate_queryset(child_qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @cache_response()
    @list_route(methods=['get'])
    def ladylist(self, request, *args, **kwargs):
        """ 获取特卖女装列表 """
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(shelf_status=Product.UP_SHELF)
        
        female_qs = self.order_queryset(request,self.get_female_qs(queryset))
        page = self.paginate_queryset(female_qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
#     @cache_response()
    @list_route(methods=['get'])
    def modellist(self, request, *args, **kwargs):
        """ 获取款式商品列表 """
        
        model_id = kwargs.get('model_id',None)
        queryset = self.filter_queryset(self.get_queryset())
        
        queryset = queryset.filter(model_id=model_id)

        serializer = self.get_serializer(queryset, many=True)
        
        return Response(serializer.data)
    
    @detail_route(methods=['get'])
    def details(self, request, *args, **kwargs):
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
    
#     @cache_response()
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
