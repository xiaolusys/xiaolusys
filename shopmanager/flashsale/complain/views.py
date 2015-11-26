# coding=utf-8
__author__ = 'timi06'
from .models import Complain
from .serializers import ComplainSerializers
from rest_framework.response import Response
from rest_framework import generics, viewsets, permissions, authentication, renderers


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
    """
    queryset = Complain.objects.all()
    serializer_class = ComplainSerializers
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def create(self, request, *args, **kwargs):
        """ 创建投诉 """
        content = request.REQUEST
        com_title = content.get('com_title', '')
        com_content = content.get('com_content', '')
        com_type = int(content.get('com_type', 3))
        complain = Complain()
        complain.insider_phone = str(request.user.id)
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