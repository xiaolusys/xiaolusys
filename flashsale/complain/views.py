# coding=utf-8
__author__ = 'yan.huang'
from .models import Complain
from .serializers import ComplainSerializers
from rest_framework.response import Response
from rest_framework import generics, viewsets, permissions, authentication, renderers
from django.shortcuts import get_object_or_404
from rest_framework.decorators import detail_route, list_route
from core.utils.modelutils import get_class_fields

from rest_framework import exceptions


class ComplainsDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Complain.objects.all()
    serializer_class = ComplainSerializers


class ComplainViewSet(viewsets.ModelViewSet):
    """
    - {prefix}/method: `get`  获取用户的投诉列表
    - {prefix}/method: `post` 创建用户的投诉条目　　
        -  com_type     类型 :   `0`: 购物问题;
                                `1`: 订单相关;
                                `2`: 意见/建议;
                                `4`: 售后问题;
                                `3`: 其他
        -  com_title    标题 default 问题反馈
        -  com_content  内容
        -  contact_way  联系方式
    - reply method: `post`  回复
    """
    queryset = Complain.objects.all()
    serializer_class = ComplainSerializers
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def create(self, request, *args, **kwargs):
        """ 创建投诉 """
        content = request.REQUEST
        com_title = content.get('com_title', '')
        com_content = content.get('com_content', '')
        com_type = int(content.get('com_type', 3))
        complain = Complain()
        complain.user_id = str(request.user.id)
        complain.com_title = com_title
        complain.com_content = com_content
        complain.com_type = com_type
        complain.save()
        return Response({"res": True})

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=["get"])
    def history_complains(self, request):
        content = request.REQUEST
        condition = {}
        fields = get_class_fields(Complain)
        for f in fields:
            if f in content:
                condition[f] = content.get(f)
        queryset = Complain.objects.filter(user_id=request.user.id).filter(**condition).order_by('-id')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=["post"])
    def reply(self, request, pk=None):
        content = request.REQUEST
        id = content.get('id', '')
        complain = get_object_or_404(Complain, id=id)
        reply = content.get('reply', '')
        complain.respond(request.user.username, reply)
        return Response({"res": True})

    @detail_route(methods=["post"])
    def close(self, request, pk=None):
        complain = get_object_or_404(Complain, id=pk)
        complain.close(request.user.username)
        return Response({"res": True})