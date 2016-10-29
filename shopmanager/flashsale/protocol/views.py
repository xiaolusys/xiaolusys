# coding=utf-8
import datetime
import django_filters

from rest_framework import status
from rest_framework import authentication
from rest_framework import filters
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions

from flashsale.protocol import serializers
from flashsale.protocol.models import APPFullPushMessge
from apis.v1.dailypush.apppushmsg import create_app_push_msg, delete_app_push_msg_by_id, update_app_push_msg_by_id, \
    push_msg_right_now_by_id


class APPFullPushMessgeFilter(filters.FilterSet):
    class Meta:
        model = APPFullPushMessge
        fields = [
            'push_time',
            'status'
        ]


class APPFullPushMessgeViewSet(viewsets.ModelViewSet):
    queryset = APPFullPushMessge.objects.all().order_by('-push_time')
    serializer_class = serializers.APPPushMessgeSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, permissions.DjangoModelPermissions)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = APPFullPushMessgeFilter

    @list_route(methods=['get'])
    def list_filters(self, request, *args, **kwargs):
        return Response({
            'status': APPFullPushMessge.STATUSES,
            'target_url': APPFullPushMessge.TARGET_CHOICES,
            'platform': APPFullPushMessge.PLATFORM_CHOICES,
        })

    def create(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        try:
            desc = request.data.pop('desc')
            platform = request.data.pop('platform')
            push_time = datetime.datetime.strptime(request.data.pop('push_time'),
                                                   '%Y-%m-%d %H:%M:%S')
            p = create_app_push_msg(desc, platform, push_time, **request.data)
        except Exception as e:
            raise exceptions.APIException(e.message)
        serializer = self.get_serializer(p)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        try:
            delete_app_push_msg_by_id(int(kwargs.get('pk')))
        except Exception as e:
            raise exceptions.APIException(e.message)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        try:
            push_time = datetime.datetime.strptime(request.data.pop('push_time'),
                                                   '%Y-%m-%d %H:%M:%S')
            request.data.update({'push_time': push_time})
            update_app_push_msg_by_id(int(kwargs.get('pk')), **request.data)
            instance = self.get_object()
            serializer = self.get_serializer(instance)
        except Exception as e:
            raise exceptions.APIException(e.message)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def push_msg(self, request, *args, **kwargs):
        # type: (HttpRequest, *Any, **Any) -> Response
        """推送指定记录
        """
        flag = push_msg_right_now_by_id(int(kwargs.get('pk')))
        code = 0 if flag else 1
        info = '操作成功' if flag else '操作出错'
        return Response({'code': code, 'info': info})
