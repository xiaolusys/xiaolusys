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
from rest_framework.views import APIView

from flashsale.restpro import permissions as perms
from . import serializers
from flashsale.pay.models import Customer

from django.db.models import Sum, Count

from flashsale.xiaolumm.models_fortune import MamaFortune, CarryRecord, ActiveValue, OrderCarry, ClickCarry, AwardCarry,ReferalRelationship,GroupRelationship, UniqueVisitor


def get_mama_id(user):
    customers = Customer.objects.filter(user=user)
    mama_id = None
    if customers.count() > 0:
        customer = customers[0]
        xlmm = customer.getXiaolumm()
        if xlmm:
            mama_id = xlmm.id
    mama_id=1
    return mama_id


def get_recent_days_carrysum(queryset, mama_id, from_date, end_date, sum_field):
    query_set = queryset.filter(mama_id=mama_id, date_field__gte=from_date,
                                date_field__lte=end_date).values('date_field').annotate(today_carry=Sum(sum_field))
    sum_dict = {}
    for entry in query_set:
        key = entry["date_field"]
        sum_dict[key] = entry["today_carry"]
    return sum_dict


def add_day_carry(datalist, queryset, sum_field, scale=0.01):
    """
    计算求和字段按
    照日期分组
    添加到<today_carry>字段　的　值
    """
    mama_id = datalist[0].mama_id
    end_date = datalist[0].date_field
    from_date = datalist[-1].date_field
    ### search database to group dates and get carry_num for each group
    sum_dict = get_recent_days_carrysum(queryset, mama_id, from_date, end_date, sum_field)
    for entry in datalist:
        key = entry.date_field
        if key in sum_dict:
            entry.today_carry = sum_dict[key] * scale


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
        # we dont return canceled record
        return self.queryset.filter(mama_id=mama_id).exclude(status=3).order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)
        sum_field = 'carry_num'
        if len(datalist) > 0:
            add_day_carry(datalist, self.queryset, sum_field)
        serializer = serializers.CarryRecordSerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class OrderCarryViewSet(viewsets.ModelViewSet):
    """
    return mama's order list (including web/app direct orders, and referal's orders).
    with parameter "?carry_type=direct", will return only direct orders.
    """
    queryset = OrderCarry.objects.all()
    page_size = 10
    serializer_class = serializers.OrderCarrySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        carry_type = request.REQUEST.get("carry_type", "all")
        if carry_type == "direct":
            return self.queryset.filter(mama_id=mama_id).order_by('-date_field', '-created')
        # we dont return upaid/canceled order
        return self.queryset.filter(mama_id=mama_id).exclude(status=0).exclude(status=3).order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        ### find from_date and end_date in datalist
        mama_id, from_date, end_date = None, 0, 0
        if len(datalist) > 0:
            sum_field = 'carry_num'
            add_day_carry(datalist, self.queryset, sum_field)
        serializer = serializers.OrderCarrySerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

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
        return self.queryset.filter(mama_id=mama_id).order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)
        if len(datalist) > 0:
            sum_field = 'total_value'
            add_day_carry(datalist, self.queryset, sum_field)

        serializer = serializers.ClickCarrySerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

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
        return self.queryset.filter(mama_id=mama_id).order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        if len(datalist) > 0:
            sum_field = 'carry_num'
            add_day_carry(datalist, self.queryset, sum_field)
        serializer = serializers.AwardCarrySerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

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
        return self.queryset.filter(mama_id=mama_id).order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        if len(datalist) > 0:
            sum_field = 'value_num'
            add_day_carry(datalist, self.queryset, sum_field, scale=1)

        serializer = serializers.ActiveValueSerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class ReferalRelationshipViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = ReferalRelationship.objects.all()
    serializer_class = serializers.ReferalRelationshipSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(referal_from_mama_id=mama_id).order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        serializer = serializers.ReferalRelationshipSerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


class GroupRelationshipViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = GroupRelationship.objects.all()
    serializer_class = serializers.GroupRelationshipSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(leader_mama_id=mama_id).order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        serializer = serializers.GroupRelationshipSerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')



class UniqueVisitorViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = UniqueVisitor.objects.all()
    serializer_class = serializers.UniqueVisitorSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        mama_id = get_mama_id(request.user)
        return self.queryset.filter(mama_id=mama_id).order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        serializer = serializers.UniqueVisitorSerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')


def match_data(from_date, end_date, visitors, orders):
    """
    match visitors/orders data according to date range.
    """
    data = []
    i,j = 0,0
    maxi,maxj = len(visitors), len(orders)
    
    from_date = from_date + datetime.timedelta(1)
    while from_date <= end_date:
        visitor_num, order_num, carry = 0,0,0
        if i < maxi and visitors[i]["date_field"] == from_date:
            visitor_num = visitors[i]["visitor_num"]
            i += 1
            
        if j < maxj and orders[j]["date_field"] == from_date:
            order_num, carry = orders[j]["order_num"], orders[j]["carry"]
            j += 1
            
        entry = {"date_field":from_date, "visitor_num":visitor_num, 
                 "order_num": order_num, "carry":float('%.2f' % (carry * 0.01))}
        data.append(entry)
        from_date += datetime.timedelta(1)
    return data


class OrderCarryVisitorView(APIView):
    """
    given from=2 and days=5, we find out all 5 days' data, starting
    from 2 days ago, backing to 7 days ago.
    """
    queryset = UniqueVisitor.objects.all()
    page_size = 10
    serializer_class = serializers.UniqueVisitorSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get(self, request):
        content = request.REQUEST
        days_from = int(content.get("from",0))
        days_length   = int(content.get("days",1))

        mama_id = get_mama_id(request.user)

        today_date = datetime.datetime.now().date()
        end_date = today_date - datetime.timedelta(days_from)
        from_date = today_date - datetime.timedelta(days_from+days_length)

        visitors = self.queryset.filter(mama_id=mama_id, date_field__gt=from_date, date_field__lte=end_date).order_by('date_field').values('date_field').annotate(visitor_num=Count('pk'))
        orders = OrderCarry.objects.filter(mama_id=mama_id,date_field__gt=from_date,date_field__lte=end_date).order_by('date_field').values('date_field').annotate(order_num=Count('pk'),carry=Sum('carry_num'))

        data = match_data(from_date, end_date, visitors, orders)
        return Response(data)

