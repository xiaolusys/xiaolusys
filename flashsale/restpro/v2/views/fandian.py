# encoding=utf8
from datetime import datetime, timedelta
from rest_framework import viewsets
from rest_framework import authentication
from rest_framework.response import Response

from common.auth import WeAppAuthentication
from flashsale.pay.models.user import Customer, BudgetLog
from flashsale.restpro.v2.serializers.serializers import BudgetLogSerialize


class FandianViewSet(viewsets.GenericViewSet):
    """
    """
    authentication_classes = (authentication.SessionAuthentication, WeAppAuthentication, authentication.BasicAuthentication)
    serializer_class = BudgetLogSerialize

    def index(self, request, *args, **kwargs):
        """
        GET /rest/v2/rebate

        当月所有有返点记录
        """
        today = datetime.today()
        thismonth = datetime(today.year, today.month, 1)
        lastmonth = thismonth - timedelta(days=1)
        month = lastmonth.strftime('%Y%m')

        queryset = BudgetLog.objects.filter(
            budget_log_type=BudgetLog.BG_FANDIAN,
            uni_key__contains='fd-{month}'.format(month=month)
        ).order_by('-flow_amount')

        queryset = self.paginate_queryset(queryset)
        serializers = self.get_serializer(queryset, many=True)
        return self.get_paginated_response(serializers.data)

    def history(self, req, *args, **kwargs):
        """
        GET /rest/v2/rebate/history

        某人历史所有返点
        """
        customer = Customer.getCustomerByUser(user=req.user)

        if not customer:
            return Response({"code": 1, "info": u"没有登录"})

        queryset = BudgetLog.objects.filter(
            budget_log_type=BudgetLog.BG_FANDIAN,
            customer_id = customer.id
        ).order_by('-created')

        queryset = self.paginate_queryset(queryset)
        serializers = self.get_serializer(queryset, many=True)
        return self.get_paginated_response(serializers.data)
