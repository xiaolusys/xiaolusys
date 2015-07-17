# -*- coding:utf8 -*-
import datetime
from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status

from shopback.items.models import Product
from flashsale.pay.models import GoodShelf

from . import permissions as perms
from . import serializers 


class PosterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
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
    
    

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    
    - {prefix}/previous[.format]: allow users to get last sale list;
    
    - {prefix}/advance[.format]: allow users to get future sale list;
    """
    queryset = Product.objects.filter(status=Product.NORMAL,shelf_status=Product.UP_SHELF)
    serializer_class = serializers.ProductSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    
    @list_route(methods=['get'])
    def previous(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        queryset = queryset.filter(sale_time__lt=datetime.date.today())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
 
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @list_route(methods=['get'])
    def advance(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        queryset = queryset.filter(sale_time__gt=datetime.date.today())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
 
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    
    def get_female_qs(self,queryset):
        
        return queryset.filter(outer_id__startswith='8')
    
    def get_child_qs(self,queryset):
        
        return queryset.filter(outer_id__startswith='9')
    
    @list_route(methods=['get'])
    def promote_today(self, request, *args, **kwargs):
        
        target_date = datetime.date.today()
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(sale_time=target_date).order_by('-details__is_recommend')
        
        female_qs = self.get_female_qs(queryset)
        men_qs  = self.get_child_qs(queryset)
        
        response_date = {'female_list':self.get_serializer(female_qs, many=True).data,
                         'child_list':self.get_serializer(men_qs, many=True).data}
        
        return Response(response_date)
    
    @list_route(methods=['get'])
    def promote_previous(self, request, *args, **kwargs):
        
        target_date = datetime.date.today() - datetime.timedelta(days=1)        
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(sale_time=target_date).order_by('-details__is_recommend')
        
        female_qs = self.get_female_qs(queryset)
        men_qs  = self.get_child_qs(queryset)
        
        response_date = {'female_list':self.get_serializer(female_qs, many=True).data,
                         'child_list':self.get_serializer(men_qs, many=True).data}
        
        return Response(response_date)
    
    
    
    