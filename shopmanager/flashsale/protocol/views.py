# coding=utf-8
import datetime
import django_filters

from rest_framework import status
from rest_framework import authentication
from rest_framework import filters
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework import exceptions

from flashsale.protocol import serializers
from flashsale.protocol.models import APPFullPushMessge
from apis.v1.dailypush.apppushmsg import *


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
            "target_url": APPFullPushMessge.TARGET_CHOICES,
            "platform": APPFullPushMessge.PLATFORM_CHOICES,
        })

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # self.perform_destroy(instance)
        raise exceptions.APIException(u'不予删除操作!')
        # return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
