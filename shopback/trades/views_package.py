# coding=utf-8
from rest_framework import generics, permissions, renderers, viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions
from django.shortcuts import get_object_or_404

from shopback.trades.models import PackageOrder
from shopback.trades.serializers import PackageOrderSerializer


class PackageOrder(viewsets.ModelViewSet):
    queryset = PackageOrder.objects.all()
    serializer_class = PackageOrderSerializer
    # authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    # permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    @list_route(methods=['get'])
    def edit(self, request):
