# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework import authentication, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from flashsale.pay.models import Envelop, BankAccount, UserBudget
from flashsale.pay.models.user import Customer
from flashsale.restpro.v2.serializers.envelop import EnvelopSerializer

import logging
logger = logging.getLogger(__name__)

class EnvelopViewSet(viewsets.ReadOnlyModelViewSet):
    """
    > ### /budget_cash_out: 转账接口　
    - cashout_amount  必填，提现金额（单位：元）
    - channel  选填，可选项（wx：提现请求来源于微信公众号, wx_transfer: 使用微信企业转账, sandpay: 银行卡转账）
    - name 收款人姓名(必须和微信绑定的银行卡姓名一致)(当channel是wx_transfer时必填.其他选填.)
    - card_id 当channel 为sandpay　时必须传入, 可通过 /rest/v2/bankcards/get_default 获取默认转账银行卡ID
    返回：
        {'code': xx, 'message': xxx, 'qrcode': xxx}
    - 返回`code`:
        0 成功;
        1　提现金额小于0;
        2 提现金额大于当前账户金额;
        3 参数错误;
        4　用户没有公众号账号;
        5　用户unionid不存在
        6 提现不能超过200
        11　已经提现过一次无审核２元
    """
    queryset = Envelop.objects.all()
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = EnvelopSerializer

    def get_customer_envelops(self, request):
        customer = Customer.objects.filter(user=request.user).first()
        return self.get_queryset().filter(customer_id=customer.id)

    def list(self, request, *args, **kwargs):
        queryset = self.get_customer_envelops(request)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk, *args, **kwargs):
        customer = Customer.objects.filter(user=request.user).first()
        instance = get_object_or_404(Envelop, customer_id=customer.id, pk=pk)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @list_route(methods=['post'])
    def budget_cash_out(self, request):
        """
        钱包提现接口
        POST /rest/v2/users/budget_cash_out
        参数：
        - cashout_amount  必填，提现金额（单位：元）
        - channel  选填，可选项（wx：提现请求来源于微信公众号, wx_transfer: 使用微信企业转账, sandpay: 银行卡转账）
        - name 收款人姓名(必须和微信绑定的银行卡姓名一致)(当channel是wx_transfer时必填.其他选填.)
        - card_id 当channel 为sandpay　时必须传入, 可通过 /rest/v2/bankcards/get_default 获取默认转账银行卡ID
        返回：
        {'code': xx, 'message': xxx, 'qrcode': xxx}
        - 返回`code`:
            0 成功;
            1　提现金额小于0;
            2 提现金额大于当前账户金额;
            3 参数错误;
            4　用户没有公众号账号;
            5　用户unionid不存在
            6 提现不能超过200
           11　已经提现过一次无审核２元
        """
        content = request.data
        cashout_amount = content.get('cashout_amount', None)
        channel = content.get('channel', None)
        name = content.get('name', None)
        verify_code = content.get('verify_code', None)
        card_id = content.get('card_id', None)

        if not cashout_amount:
            return Response({'code': 3, 'message': '参数错误', 'qrcode': ''})

        customer = get_object_or_404(Customer, user=request.user)
        if not customer.status == Customer.NORMAL:
            info = u'你的帐号已被冻结，请联系管理员！'
            return Response({"code": 10, "message": info, "info": info})

        if channel == Envelop.SANDPAY and not card_id:
            info = u'请选择需要转账的银行卡！'
            return Response({"code": 20, "message": info, "info": info})

        if channel == Envelop.SANDPAY:
            bank_card = BankAccount.objects.filter(user=request.user, id=card_id).first()
            if not bank_card:
                info = u'当前用户没有该银行卡记录'
                logger.error('%s: account_id=%s, user_id=%s' % (info, card_id, request.user.id))
                return Response({"code": 20, "message": info, "info": info})

        budget = get_object_or_404(UserBudget, user=customer)
        amount = int(float(cashout_amount) * 100)  # 以分为单位(提现金额乘以100取整)

        code, info = budget.action_budget_cashout(
            amount, verify_code=verify_code, channel=channel, name=name, card_id=card_id)

        qrcode = ''
        return Response({'code': code, "message": info, "info": info, "qrcode": qrcode})





