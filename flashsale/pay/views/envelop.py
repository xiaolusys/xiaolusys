# coding=utf-8
import decimal
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Sum
from django.conf import settings
from django.views.generic import View

from rest_framework.renderers import JSONRenderer
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from core.options import log_action, ADDITION, CHANGE
from flashsale.pay.models import Envelop, BudgetLog, UserBudget


class EnvelopConfirmSendView(View):
    renderer_classes = (JSONRenderer,)

    def post(self, request, *args, **kwargs):

        content = request.POST
        origin_url = content.get('origin_url')
        envelop_ids = content.get('envelop_ids', '').split(',')
        secret = content.get('secret')

        admin_email = settings.MANAGERS[0][1]
        if secret.strip() != admin_email:
            messages.add_message(request, messages.ERROR, u'请输入正确的红包发送暗号！')
            return redirect(origin_url)

        envelop_qs = Envelop.objects.filter(id__in=envelop_ids, status__in=(Envelop.WAIT_SEND, Envelop.FAIL))

        try:
            for envelop in envelop_qs:
                envelop.send_envelop()
                log_action(request.user.id, envelop, CHANGE, u'发送红包')
        except Exception, exc:
            messages.add_message(request, messages.ERROR, u'红包发送异常:%s' % (exc.message))

        envelop_goodqs = Envelop.objects.filter(id__in=envelop_ids, status=Envelop.CONFIRM_SEND)
        envelop_count = envelop_goodqs.count()
        total_amount = envelop_goodqs.aggregate(total_amount=Sum('amount')).get('total_amount') or 0

        messages.add_message(request, messages.INFO, u'已成功发送 %s 个红包，总金额：%s！' % (envelop_count, total_amount / 100.0))

        return redirect(origin_url)


class SendBudgetEnvelopAPIView(APIView):
    """发送红包: 创建用户budget_log记录
    """
    queryset = UserBudget.objects.all()
    renderer_classes = (JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser, permissions.DjangoModelPermissions)

    def get_budget_data(self, customer_id):
        # type: (int) -> UserBudget
        budget = self.queryset.filter(user_id=customer_id).first()
        data = {'id': budget.id,
                'customer_id': customer_id,
                'nick': budget.user.nick,
                'mobile': budget.user.mobile,
                'cash': budget.budget_cash}
        return data

    def get(self, request):
        # type: (HttpRequest) -> Response
        """获取用户钱包信息
        """
        content = request.GET or request.data
        customer_id = content.get('customer_id') or None
        customer_id = int(customer_id)
        try:
            data = self.get_budget_data(customer_id)
        except Exception as e:
            return Response({'code': 1, 'info': '账户异常:%s' % e.message, 'data': {}})
        return Response({'code': 0, 'info': 'success', 'data': data})

    def post(self, request):
        # type: (HttpRequest) -> Response
        """发送红包
        """
        content = request.POST or request.data
        customer_id = content.get('customer_id') or None
        customer_id = int(customer_id)
        amount = content.get('amount') or '0'
        memo = content.get('memo') or None

        flow_amount = int(decimal.Decimal(amount) * 100)  # 以分为单位
        if flow_amount == 0:
            return Response({'code': 1, 'info': '红包金额不能为0', 'data': self.get_budget_data(customer_id)})

        # 添加红包钱包记录
        budget_log = BudgetLog.create(customer_id=int(customer_id),
                                      budget_type=BudgetLog.BUDGET_IN,
                                      flow_amount=flow_amount,
                                      budget_log_type=BudgetLog.BG_ENVELOPE)
        log_action(request.user, budget_log, ADDITION, u'赠送红包 %s' % memo)

        data = self.get_budget_data(customer_id)
        return Response({'code': 0, 'info': 'success', 'data': data})
