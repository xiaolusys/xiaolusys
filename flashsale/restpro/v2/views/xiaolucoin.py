# encoding=utf8
from rest_framework import viewsets
from rest_framework import authentication, permissions
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from django.db import IntegrityError

from common.auth import WeAppAuthentication, perm_required
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

    @perm_required('xiaolumm.manage_xiaolu_coin')
    def balance(self, req, *args, **kwargs):
        """
        GET /apis/xiaolumm/xiaolucoin/balance

        - mama_id
        """
        mama_id = req.GET.get('mama_id') or ''

        if not mama_id:
            return Response({'code': 1, 'msg': '找不到mama_id'})
        coin = XiaoluCoin.get_or_create(mama_id)

        return Response({'balance': coin.amount, 'mama_id': mama_id})

    @perm_required('xiaolumm.manage_xiaolu_coin')
    def change(self, request, *args, **kwargs):
        """
        POST /rest/v2/xiaolucoin/change

        - amount 金额(分),负数则减少余额,正数增加余额
        - mama_id
        - subject 收支类型['gift', 'refund', 'recharge', 'consume']
        - referal_id (可选) 引用id

        增加,减少小鹿币余额
        """
        content = request.POST or request.data
        mama_id = content.get('mama_id') or ''
        amount = content.get('amount') or None
        subject = content.get('subject') or None
        referal_id = content.get('referal_id') or ''

        if not amount:
            return Response({'code': 2, 'msg': '金额错误'})
        try:
            x = int(amount)
            isdigit = isinstance(x, int)
        except ValueError:
            isdigit = False
        if not isdigit:
            return Response({'code': 2, 'msg': '金额错误'})
        if x > 20000:
            return Response({'code': 2, 'msg': '超出手工操作金额，请联系管理员'})

        if subject not in dict(XiaoluCoinLog.SUBJECT_CHOICES).keys():
            return Response({'code': 3, 'msg': '收支类型错误'})

        if not mama_id:
            return Response({'code': 1, 'msg': '找不到mama_id'})
        coin = XiaoluCoin.get_or_create(mama_id)

        amount = int(amount)
        try:
            coin.change(amount, subject, referal_id=referal_id)
        except IntegrityError, exc:
            return Response({'code': 4, 'msg': '已经有相同的赠送记录，每天只能赠送一次'})
        return Response({'code': 0, 'msg': '修改成功'})
