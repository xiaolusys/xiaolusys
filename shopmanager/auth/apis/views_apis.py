# coding=utf-8
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import filters
from rest_framework.response import Response
from django.contrib.auth.models import User
from auth.apis import serializers


class UserFilter(filters.FilterSet):
    class Meta:
        model = User
        fields = ['id', 'is_staff', 'is_active', 'username']


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ### Django User API
    - [/apis/auth/v1/user?is_staff=True](/apis/auth/v1/user?is_staff=True) 过滤为员工状态的用户;
        * 可过滤字段: id, is_staff, is_active, username
    """
    queryset = User.objects.all()
    serializer_class = serializers.UserSimpleSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,
                          permissions.IsAdminUser,
                          permissions.DjangoModelPermissions)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)
    filter_class = UserFilter
