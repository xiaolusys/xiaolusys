# coding=utf-8

from rest_framework import viewsets

from common.auth import WeAppAuthentication
from . import serializers
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from django.shortcuts import get_object_or_404
from flashsale.pay.models import Customer
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from flashsale.pay.models import IntegralLog, Integral


class UserIntegralViewSet(viewsets.ModelViewSet):
    queryset = Integral.objects.all()
    serializer_class = serializers.UserIntegralSerializer
    authentication_classes = (authentication.SessionAuthentication, WeAppAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(integral_user=customer.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def get_owner_integral(self, request):
        integral = self.get_owner_queryset(request).first()
        if integral:
            integral_value = integral.integral_value
            return Response({"code": 0, "integral_value": integral_value})
        else:
            return Response({"code": 1, "integral_value": 0})


class UserIntegralLogViewSet(viewsets.ModelViewSet):
    queryset = IntegralLog.objects.all()
    serializer_class = serializers.UserIntegralLogSerializer
    authentication_classes = (authentication.SessionAuthentication, WeAppAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        return self.queryset.filter(integral_user=customer.id)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))
        # 过滤已经确定的积分
        queryset = queryset.filter(log_status=IntegralLog.CONFIRM)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
