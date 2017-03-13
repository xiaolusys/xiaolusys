# encoding=utf8
from rest_framework import viewsets
from rest_framework import authentication, permissions
from rest_framework.response import Response

from common.auth import WeAppAuthentication
from flashsale.pay.models.user import Customer
from flashsale.xiaolumm.models import XiaoluCoinLog, XiaoluCoin
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

    def change(self, req, *args, **kwargs):
        """
        POST /rest/v2/xiaolucoin/change

        - amount 金额(分),负数则减少余额,正数增加余额
        - mama_id
        - subject 收支类型['gift', 'refund', 'recharge', 'consume']
        - referal_id (可选) 引用id

        增加,减少小鹿币余额
        """
        mama_id = req.POST.get('mama_id') or ''
        amount = req.POST.get('amount') or None
        subject = req.POST.get('subject') or None
        referal_id = req.POST.get('referal_id') or ''

        if (not amount) or (not amount.isdigit()):
            return Response({'code': 2, 'msg': '金额错误'})

        if subject not in dict(XiaoluCoinLog.SUBJECT_CHOICES).keys():
            return Response({'code': 3, 'msg': '收支类型错误'})

        coin = XiaoluCoin.get_or_create(mama_id)
        if (not mama_id) or (not coin):
            return Response({'code': 1, 'msg': '找不到mama_id'})

        amount = int(amount)

        coin.change(amount, subject, referal_id=referal_id)
        return Response({'code': 0, 'msg': '修改成功'})
