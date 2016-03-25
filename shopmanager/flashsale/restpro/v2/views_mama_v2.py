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

from flashsale.xiaolumm.models_fortune import MamaFortune, CarryRecord, ActiveValue, OrderCarry, ClickCarry, AwardCarry,ReferalRelationship,GroupRelationship, UniqueVisitor, DailyStats


def get_customer_id(user):
    customers = Customer.objects.filter(user=user)
    customer_id = None
    if customers.count() > 0:
        customer_id = customers[0].id
    #customer_id = 19 # debug test
    return customer_id


def get_mama_id(user):
    customers = Customer.objects.filter(user=user)
    mama_id = None
    if customers.count() > 0:
        customer = customers[0]
        xlmm = customer.getXiaolumm()
        if xlmm:
            mama_id = xlmm.id
    #mama_id = 5 # debug test
    return mama_id


def get_recent_days_carrysum(queryset, mama_id, from_date, end_date, sum_field, exclude_statuses=None):
    qset = queryset.filter(mama_id=mama_id,date_field__gte=from_date,date_field__lte=end_date)

    if exclude_statuses:
        for ex in exclude_statuses:
            qset = qset.exclude(status=ex)
    
    qset = qset.values('date_field').annotate(today_carry=Sum(sum_field))
    sum_dict = {}
    for entry in qset:
        key = entry["date_field"]
        sum_dict[key] = entry["today_carry"]
    return sum_dict


def add_day_carry(datalist, queryset, sum_field, scale=0.01, exclude_statuses=None):
    """
    计算求和字段按
    照日期分组
    添加到<today_carry>字段　的　值
    """
    mama_id = datalist[0].mama_id
    end_date = datalist[0].date_field
    from_date = datalist[-1].date_field
    ### search database to group dates and get carry_num for each group
    sum_dict = get_recent_days_carrysum(queryset, mama_id, from_date, end_date, sum_field, exclude_statuses=exclude_statuses)
    
    for entry in datalist:
        key = entry.date_field
        if key in sum_dict:
            entry.today_carry = float('%.2f' % (sum_dict[key] * scale))


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

    def get_owner_queryset(self, request, exclude_statuses=None):
        mama_id = get_mama_id(request.user)
        qset = self.queryset.filter(mama_id=mama_id)

        # we dont return canceled record
        if exclude_statuses:
            for ex in exclude_statuses:
               qset = qset.exclude(status=ex)
               
        return qset.order_by('-date_field', '-created')


    def list(self, request, *args, **kwargs):
        exclude_statuses = [3,]
        datalist = self.get_owner_queryset(request, exclude_statuses=exclude_statuses)
        datalist = self.paginate_queryset(datalist)
        sum_field = 'carry_num'

        if len(datalist) > 0:
            add_day_carry(datalist, self.queryset, sum_field, exclude_statuses=exclude_statuses)
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

    def get_owner_queryset(self, request, carry_type, exclude_statuses=None):
        mama_id = get_mama_id(request.user)
        if carry_type == "direct":
            return self.queryset.filter(mama_id=mama_id).order_by('-date_field', '-created')
        
        qset = self.queryset.filter(mama_id=mama_id)
        if exclude_statuses:
            for ex in exclude_statuses:
                qset = qset.exclude(status=ex)
        return qset.order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        exclude_statuses = [0, 3] # not show unpaid/canceled orders

        carry_type = request.REQUEST.get("carry_type", "all")
        if carry_type == "direct":
            exclude_statuses = None # show all orders excpet indirect ones
            
        datalist = self.get_owner_queryset(request, carry_type, exclude_statuses=exclude_statuses)
        datalist = self.paginate_queryset(datalist)

        ### find from_date and end_date in datalist
        mama_id, from_date, end_date = None, 0, 0
        if len(datalist) > 0:
            sum_field = 'carry_num'
            add_day_carry(datalist, self.queryset, sum_field, exclude_statuses=exclude_statuses)
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

    def get_owner_queryset(self, request, exclude_statuses=None):
        mama_id = get_mama_id(request.user)
        qset = self.queryset.filter(mama_id=mama_id)

        # we dont return canceled record
        if exclude_statuses:
            for ex in exclude_statuses:
               qset = qset.exclude(status=ex)
               
        return qset.order_by('-date_field', '-created')

    def list(self, request, *args, **kwargs):
        exclude_statuses = [3,]
        datalist = self.get_owner_queryset(request, exclude_statuses=exclude_statuses)
        datalist = self.paginate_queryset(datalist)

        if len(datalist) > 0:
            sum_field = 'value_num'
            add_day_carry(datalist, self.queryset, sum_field, scale=1, exclude_statuses=exclude_statuses)

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
    given from=0 (or omit), we return today's visitors;
    given from=2 , we return all the visitors for 2 days ago.
    """
    
    queryset = UniqueVisitor.objects.all()
    serializer_class = serializers.UniqueVisitorSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        content = request.REQUEST
        days_from = int(content.get("from",0))
        
        date_field = datetime.datetime.now().date()
        if days_from > 0:
            date_field = date_field - datetime.timedelta(days=days_from)

        mama_id = get_mama_id(request.user)
        return self.queryset.filter(mama_id=mama_id,date_field=date_field).order_by('-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        serializer = serializers.UniqueVisitorSerializer(datalist, many=True)
        return self.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')



from flashsale.xiaolumm.models_fans import XlmmFans

class XlmmFansViewSet(viewsets.ModelViewSet):
    """
    """
    queryset = XlmmFans.objects.all()
    serializer_class = serializers.XlmmFansSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request):
        customer_id = get_customer_id(request.user)
        return self.queryset.filter(xlmm_cusid=customer_id).order_by('-created')

    def list(self, request, *args, **kwargs):
        datalist = self.get_owner_queryset(request)
        datalist = self.paginate_queryset(datalist)

        serializer = serializers.XlmmFansSerializer(datalist, many=True)
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



def fill_data(data, days_from, days_length):
    today_date = datetime.datetime.now().date()
    end_date   = today_date - datetime.timedelta(days=days_from)
    from_date  = end_date - datetime.timedelta(days=days_length-1)
    
    res = []
    i, maxi = 0, len(data)
    while from_date <= end_date:
        visitor_num, order_num, carry = 0,0,0
        if i < maxi and data[i]["date_field"] == str(from_date):
            visitor_num, order_num, carry = data[i]["today_visitor_num"], data[i]["today_order_num"], data[i]["today_carry_num"]
            i += 1
        entry = {"date_field":from_date, "visitor_num":visitor_num, "order_num": order_num, "carry":carry}
        res.append(entry)
        from_date += datetime.timedelta(1)
    
    return res



class DailyStatsViewSet(viewsets.ModelViewSet):
    """
    given from=2 and days=5, we find out all 5 days' data, starting
    from 2 days ago, backing to 7 days ago.
    
    from=x: starts from x days before
    days=n: needs n days' data
    """
    queryset = DailyStats.objects.all()
    serializer_class = serializers.DailyStatsSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer)

    def get_owner_queryset(self, request, days_from, days_length):
        mama_id = get_mama_id(request.user)

        today_date = datetime.datetime.now().date()
        end_date = today_date - datetime.timedelta(days=days_from)
        return self.queryset.filter(mama_id=mama_id, date_field__lte=end_date).order_by('-date_field','-created')[:days_length]

    def list(self, request, *args, **kwargs):
        content = request.REQUEST
        days_from = int(content.get("from",0))
        days_length   = int(content.get("days",1))

        datalist = self.get_owner_queryset(request, days_from, days_length)
        datalist = self.paginate_queryset(datalist)

        serializer = serializers.DailyStatsSerializer(datalist, many=True)
        res = fill_data(serializer.data, days_from, days_length)
        
        return self.get_paginated_response(res)

    def create(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')
    
