# coding=utf-8
import re

from django.contrib.admin.views.main import ChangeList

from core.utils.regex import REGEX_MOBILE
from flashsale.xiaolumm.models.models_fortune import OrderCarry


class OrderCarryChangeList(ChangeList):
    """ 订单佣金ADMIN CHANGELIST """

    def get_queryset(self, request):

        search_q = request.GET.get('q', '').strip()
        qs_trade = None
        from flashsale.pay.models import SaleOrder, SaleTrade

        if search_q.startswith('xd'):
            qs_trade = SaleTrade.objects.filter(tid=search_q)
        elif re.compile(REGEX_MOBILE).match(search_q):
            qs_trade = SaleTrade.objects.filter(receiver_mobile=search_q)

        if qs_trade and qs_trade.exists():
            qs_order = SaleOrder.objects.filter(sale_trade__in=qs_trade)
            order_ids = qs_order.values_list('oid', flat=True)
            if order_ids:
                return OrderCarry.objects.filter(order_id__in=order_ids)

        return super(OrderCarryChangeList, self).get_queryset(request)