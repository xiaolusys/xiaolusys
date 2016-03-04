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

from django.db.models import Sum, Count

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


def get_recent_days_carrysum(queryset, mama_id, from_date, end_date, sum_sield):
    query_set = queryset.filter(mama_id=mama_id, date_field__gte=from_date,
                                date_field__lte=end_date).values('date_field').annotate(today_carry=Sum(sum_sield))
    sum_dict = {}
    for entry in query_set:
        key = entry["date_field"]
        sum_dict[key] = entry["today_carry"]
    return sum_dict


def add_day_carry(datalist, queryset, sum_sield):
    """
    计算求和字段按
    照日期分组
    添加到<today_carry>字段　的　值
    """
    mama_id = datalist[0].mama_id
    end_date = datalist[0].date_field
    from_date = datalist[-1].date_field
    ### search database to group dates and get carry_num for each group
    sum_dict = get_recent_days_carrysum(queryset, mama_id, from_date, end_date, sum_sield)
    for entry in datalist:
        key = entry.date_field
        if key in sum_dict:
            entry.today_carry = sum_dict[key] * 0.01


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
        fortunes = self.get_owner_queryset(request)
        fortunes = self.paginate_queryset(fortunes)
        serializer = serializers.MamaFortuneSerializer(fortunes, many=True)
        data = serializer.data
        if len(data) > 0:
            res = data[0]
        else:
            res = None
        return Response({"mama_fortune": res})

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


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
        return self.queryset.filter(mama_id=mama_id, status__gt=0).order_by('-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)
        sum_sield = 'carry_num'
        if len(datalist) > 0:
            add_day_carry(datalist, self.queryset, sum_sield)
        serializer = serializers.CarryRecordSerializer(datalist, many=True)
        return Response({"carryrecord_list": serializer.data})

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class OrderCarryViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = OrderCarry.objects.all()
    page_size = 10
    serializer_class = serializers.OrderCarrySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(mama_id=mama_id).order_by('-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        ### find from_date and end_date in datalist
        mama_id, from_date, end_date = None, 0, 0
        if len(datalist) > 0:
            sum_sield = 'carry_num'
            add_day_carry(datalist, self.queryset, sum_sield)
        serializer = serializers.OrderCarrySerializer(datalist, many=True)
        return Response({"ordercarry_list": serializer.data})

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


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
        return self.queryset.filter(mama_id=mama_id).order_by('-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)
        if len(datalist) > 0:
            sum_sield = 'total_value'
            add_day_carry(datalist, self.queryset, sum_sield)

        serializer = serializers.ClickCarrySerializer(datalist, many=True)
        return Response({"clickcarry_list": serializer.data})

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


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
        return self.queryset.filter(mama_id=mama_id).order_by('-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        if len(datalist) > 0:
            sum_sield = 'award_num'
            add_day_carry(datalist, self.queryset, sum_sield)
        serializer = serializers.AwardCarrySerializer(datalist, many=True)
        return Response({"awardcarry_list": serializer.data})

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


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
        return self.queryset.filter(mama_id=mama_id).order_by('-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        if len(datalist) > 0:
            sum_sield = 'value_num'
            add_day_carry(datalist, self.queryset, sum_sield)

        serializer = serializers.ActiveValueSerializer(datalist, many=True)
        return Response({"activevalue_list": serializer.data})

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


