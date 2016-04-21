# coding: utf-8

import datetime

from django.core.management.base import BaseCommand

from flashsale.pay import REFUND_REFUSE_BUYER
from flashsale.pay.models import SaleOrder


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        for sale_order in SaleOrder.objects.filter(sale_trade__buyer_id=1, status=SaleOrder.WAIT_SELLER_SEND_GOODS, refund_status=REFUND_REFUSE_BUYER):
            sale_order.status = SaleOrder.TRADE_CLOSED
            print sale_order.id
            sale_order.save()
