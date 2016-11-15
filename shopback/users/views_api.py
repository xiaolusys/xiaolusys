# coding=utf-8
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import filters
from rest_framework.decorators import list_route
from rest_framework.response import Response
from django.contrib.auth.models import User
from . import serializers
from core import pagination


class UserFilter(filters.FilterSet):
    class Meta:
        model = User
        fields = ['id', 'is_staff', 'is_active', 'username']


class LargeResultsSetPagination(pagination.PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ### Django User API
    - [/apis/auth/v1/user?is_staff=True](/apis/auth/v1/user?is_staff=True) 过滤为员工状态的用户;
        * 可过滤字段: id, is_staff, is_active, username
    - [/apis/auth/v1/user/current_user](/apis/auth/v1/user/current_user) 当前用户信息;
        * method: get
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
    pagination_class = LargeResultsSetPagination

    @list_route(methods=['get'])
    def current_user(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)
