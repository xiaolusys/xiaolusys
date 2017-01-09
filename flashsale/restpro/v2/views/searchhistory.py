# coding=utf-8
from __future__ import unicode_literals, absolute_import
from rest_framework import viewsets
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions
from rest_framework import filters
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.decorators import detail_route, list_route
from rest_framework.decorators import parser_classes
from rest_framework.response import Response
from .. import serializers
from flashsale.pay.models import UserSearchHistory
from flashsale.pay.apis.v1.usersearchhistory import get_distinct_user_search_product_history_by_user_id, \
    clear_user_search_history

import logging

logger = logging.getLogger(__name__)


class UserSearchHistoryFilter(filters.FilterSet):
    class Meta:
        model = UserSearchHistory


class UserSearchHistoryViewSet(viewsets.ModelViewSet):
    """用户搜索历史 记录
    """
    queryset = UserSearchHistory.objects.all()
    serializer_class = serializers.UserSearchHistorySerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication, )
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer, )
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = UserSearchHistoryFilter

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    def destroy(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    def retrieve(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED!')

    @list_route(methods=['get'])
    def product_search_history(self, request, *args, **kwargs):
        """当前用户的 款式搜索历史
        """
        queryset = get_distinct_user_search_product_history_by_user_id(request.user.id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['post', 'get'])
    def clear_search_history(self, request, *args, **kwargs):
        content = request.POST or request.data or request.GET
        user_id = request.user.id
        target = content.get('target') or ''
        if not target:
            return Response({'code': 1, 'info': '参数错误!'})
        clear_user_search_history(user_id, target)
        return Response({'code': 0, 'info': '清楚成功!'})
