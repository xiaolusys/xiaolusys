# -*- coding:utf-8 -*-
from rest_framework import filters
from rest_framework import viewsets
from rest_framework import authentication
from rest_framework import permissions, exceptions
from rest_framework import status as rest_status
from rest_framework.response import Response
from rest_framework.decorators import list_route, detail_route
from flashsale.pay.models import ModelProduct, Customer, CuShopPros
from flashsale.restpro.v2 import serializers as serializers_v2
from pms.supplier.serializers import ModelProductSerializer
from django.shortcuts import get_object_or_404, Http404

import logging

logger = logging.getLogger(__name__)

CACHE_VIEW_TIMEOUT = 30


class ModelProductViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = ModelProduct.objects.all()
    serializer_class = serializers_v2.SimpleModelProductSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, permissions.DjangoModelPermissions)
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter,)

    def create(self, request, *args, **kwargs):
        serializer = serializers_v2.CreateModelProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            model_product = serializer.save(serializer.data, request.user)
            serializers_v2.SimpleModelProductSerializer(model_product)
            return Response(serializer.data, status=rest_status.HTTP_201_CREATED)
        except Exception, e0:
            raise exceptions.APIException(e0.message)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = serializers_v2.CreateModelProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(serializer.data, request.user, instance=instance)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # refresh the instance from the database.
            instance = self.get_object()
            serializer = self.get_serializer(instance)

        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ModelProductSerializer(instance)
        return Response(serializer.data)

    @detail_route(methods=['post'])
    def set_pictures(self, request, pk, *args, **kwargs):
        mproduct = get_object_or_404(ModelProduct, pk=pk)
        serializer = serializers_v2.ProductPictureSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mproduct = serializer.save(serializer.data, mproduct)
        serializer = self.get_serializer(mproduct)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def get_headimg(self, request, *args, **kwargs):
        """ 查询头图接口 """
        modelId = request.GET.get('modelId', '')
        if not modelId.isdigit():
            raise Http404
        from apis.v1.products import ModelProductCtl
        obj = ModelProductCtl.retrieve(modelId)
        data = serializers_v2.APIModelProductListSerializer(obj).data
        return Response([data])
