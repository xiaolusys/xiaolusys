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

from flashsale.xiaolumm.models_fortune import MamaFortune, CarryRecord, ActiveValue, OrderCarry, ClickCarry, AwardCarry


def get_mama_id(user):
    customers = Customer.objects.filter(user=user)
    
    mama_id = None
    mama_id = 5  # debug test
    
    if customers.count() > 0:
        customer = customers[0]
        xlmm = customer.getXiaolumm()
        if xlmm:
            mama_id = xlmm.id

    return mama_id


class MamaFortuneViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = MamaFortune.objects.all()
    serializer_class = serializers.MamaFortuneSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
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


class CarryRecordViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = CarryRecord.objects.all()
    serializer_class = serializers.CarryRecordSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(mama_id=mama_id)
    
    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    @list_route(methods=['get'])
    def carryrecord_list(self, request):
        datalist = self.get_owner_queryset(request)
        serializer = serializers.CarryRecordSerializer(datalist, many=True)
        data = serializer.data
        if len(data) > 0:
            res = data[0]
        else:
            res = None
        return Response({"carryrecord_list": res})


class OrderCarryViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = OrderCarry.objects.all()
    serializer_class = serializers.OrderCarrySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(mama_id=mama_id)
    
    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    @list_route(methods=['get'])
    def ordercarry_list(self, request):
        datalist = self.get_owner_queryset(request)
        serializer = serializers.OrderCarrySerializer(datalist, many=True)
        data = serializer.data
        if len(data) > 0:
            res = data[0]
        else:
            res = None
        return Response({"ordercarry_list": res})

    

class ClickCarryViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = ClickCarry.objects.all()
    serializer_class = serializers.ClickCarrySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(mama_id=mama_id)
    
    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    @list_route(methods=['get'])
    def clickcarry_list(self, request):
        datalist = self.get_owner_queryset(request)
        serializer = serializers.ClickCarrySerializer(datalist, many=True)
        data = serializer.data
        if len(data) > 0:
            res = data[0]
        else:
            res = None
        return Response({"clickcarry_list": res})


class AwardCarryViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = AwardCarry.objects.all()
    serializer_class = serializers.AwardCarrySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(mama_id=mama_id)
    
    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    @list_route(methods=['get'])
    def awardcarry_list(self, request):
        datalist = self.get_owner_queryset(request)
        serializer = serializers.AwardCarrySerializer(datalist, many=True)
        data = serializer.data
        if len(data) > 0:
            res = data[0]
        else:
            res = None
        return Response({"awardcarry_list": res})

    

class ClickCarryViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = ClickCarry.objects.all()
    serializer_class = serializers.ClickCarrySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(mama_id=mama_id)
    
    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    @list_route(methods=['get'])
    def clickcarry_list(self, request):
        datalist = self.get_owner_queryset(request)
        serializer = serializers.ClickCarrySerializer(datalist, many=True)
        data = serializer.data
        if len(data) > 0:
            res = data[0]
        else:
            res = None
        return Response({"clickcarry_list": res})


class ActiveValueViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = ActiveValue.objects.all()
    serializer_class = serializers.ActiveValueSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(mama_id=mama_id)
    
    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    @list_route(methods=['get'])
    def activevalue_list(self, request):
        datalist = self.get_owner_queryset(request)
        serializer = serializers.ActiveValueSerializer(datalist, many=True)
        data = serializer.data
        if len(data) > 0:
            res = data[0]
        else:
            res = None
        return Response({"activevalue_list": res})

