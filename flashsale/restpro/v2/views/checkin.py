# encoding=utf8
from datetime import date
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import (
    authentication,
    permissions,
    exceptions,
)

from flashsale.pay.models.checkin import Checkin
from flashsale.pay.models.user import Customer
from flashsale.restpro.v2.serializers.checkin import CheckinSerialize


class CheckinViewSet(viewsets.ModelViewSet):
    """
    ## GET /rest/v2/checkin 获取用户签到历史

    ## POST /rest/v2/checkin 签到
    """

    queryset = Checkin.objects.all()
    serializer_class = CheckinSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        customer = Customer.getCustomerByUser(user=request.user)

        if not customer:
            return Response({"code": 7, "info": u"用户未找到"})  # 登录过期

        queryset = self.queryset.filter(customer_id=customer.id).order_by('-created')
        queryset = self.paginate_queryset(queryset)
        serializers = self.get_serializer(queryset, many=True)
        return self.get_paginated_response(serializers.data)

    def create(self, request, *args, **kwargs):
        customer = Customer.getCustomerByUser(user=request.user)
        if not customer:
            return Response({"code": 7, "info": u"用户未找到"})  # 登录过期

        today = date.today()
        checkin = Checkin.objects.filter(customer=customer, created__gte=today).exists()
        if checkin:
            return Response({"code": 1, "info": u"今天已经签到过了"})

        Checkin.objects.create(customer=customer)
        return Response({"code": 0, "info": u"签到成功"})

    def retrieve(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def destroy(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')
