# coding=utf-8
import os, settings, urlparse
import datetime

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import exceptions

from flashsale.restpro import permissions as perms
from . import serializers
from flashsale.pay.models import Customer

from flashsale.xiaolumm.models_fortune import MamaFortune


class MamaFortuneViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = MamaFortune.objects.all()
    serializer_class = serializers.MamaFortuneSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        xlmm = customer.getXiaolumm()
        mama_id = None
        mama_id = 5  # test
        if xlmm:
            mama_id = xlmm.id
        return self.queryset.filter(mama_id=mama_id)

    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    @list_route(methods=['get'])
    def mama_fortune(self, request):
        fortunes = self.get_owner_queryset(request)
        serializer = serializers.MamaFortuneSerializer(fortunes, many=True)
        data = serializer.data
        if len(data) > 0:
            res = data[0]
        else:
            res = None
        return Response({"mama_fortune": res})
