# coding=utf-8
__author__ = 'yan.huang'
from flashsale.xiaolumm.models.message import XlmmMessage
from flashsale.xiaolumm.serializers import XlmmMessageSerializers
from rest_framework.response import Response
from rest_framework import exceptions
from rest_framework import generics, viewsets, permissions, authentication, renderers
from django.shortcuts import get_object_or_404
from rest_framework.decorators import detail_route, list_route
from core.utils.modelutils import get_class_fields
from collections import OrderedDict

from flashsale.xiaolumm.tasks import task_mama_daily_tab_visit_stats
from flashsale.xiaolumm.models import MamaTabVisitStats

class XlmmMessageViewSet(viewsets.GenericViewSet, viewsets.mixins.ListModelMixin):
    """
    - list: `get`  小鹿妈妈消息
    - self_list: `get` 获取自己的小鹿妈妈消息
    - <messageid>/read: `get` 设置消息为已读
    """
    queryset = XlmmMessage.objects.filter(dest=None)
    serializer_class = XlmmMessageSerializers
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @list_route(methods=['get'])
    def self_list(self, request):
        try:
            mama = request.user.customer.get_xiaolumm()
        except:
            raise exceptions.ValidationError(u'您并非登录小鹿妈妈或小鹿妈妈账号存在异常')
        if not mama:
            raise exceptions.ValidationError(u'您并非登录小鹿妈妈或小鹿妈妈账号存在异常')

        queryset, unread_cnt = XlmmMessage.get_msg_list(mama.id)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        res = self.get_paginated_response(serializer.data)
        res.data['unread_cnt'] = unread_cnt
        return res

    @list_route(methods=['get'])
    def read_list(self, request):
        try:
            mama = request.user.customer.get_xiaolumm()
        except:
            raise exceptions.ValidationError(u'您并非登录小鹿妈妈或小鹿妈妈账号存在异常')
        if not mama:
            raise exceptions.ValidationError(u'您并非登录小鹿妈妈或小鹿妈妈账号存在异常')

        task_mama_daily_tab_visit_stats.delay(mama.id, MamaTabVisitStats.TAB_NOTIFICATION)
        
        XlmmMessage.set_all_read(mama)        
        queryset, unread_cnt = XlmmMessage.get_msg_list(mama.id)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        res = self.get_paginated_response(serializer.data)
        res.data['unread_cnt'] = unread_cnt
        return res
        
    
    @detail_route(methods=['GET', 'POST'])
    def read(self, request, pk):
        try:
            mama = request.user.customer.get_xiaolumm()
        except:
            raise exceptions.ValidationError(u'您并非登录小鹿妈妈或小鹿妈妈账号存在异常')
        if not mama:
            raise exceptions.ValidationError(u'您并非登录小鹿妈妈或小鹿妈妈账号存在异常')
        message = get_object_or_404(XlmmMessage, pk=pk)
        if message.dest and message.dest != mama:
            raise exceptions.ValidationError(u'无法修改和自己无关的消息')
        XlmmMessage.set_all_read(mama)
        # message.set_read(mama)
        return Response({'id': message.id})
