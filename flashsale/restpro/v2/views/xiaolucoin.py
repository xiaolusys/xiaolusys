# encoding=utf8
from rest_framework import viewsets
from rest_framework import authentication, permissions

from common.auth import WeAppAuthentication
from flashsale.pay.models.user import Customer
from flashsale.xiaolumm.models import XiaoluCoinLog
from flashsale.restpro.v2.serializers.serializers import XiaoluCoinLogSerializer


class XiaoluCoinViewSet(viewsets.GenericViewSet):
    """
    """
    authentication_classes = (authentication.SessionAuthentication, WeAppAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = XiaoluCoinLogSerializer

    def history(self, request, *args, **kwargs):
        """
        GET /rest/v2/xiaolucoin/history

        小鹿币收支记录
        """
        customer = Customer.getCustomerByUser(user=request.user)
        mama_id = customer.mama_id

        queryset = XiaoluCoinLog.objects.filter(mama_id=mama_id).order_by('-created')

        queryset = self.paginate_queryset(queryset)
        serializers = self.get_serializer(queryset, many=True)
        return self.get_paginated_response(serializers.data)
