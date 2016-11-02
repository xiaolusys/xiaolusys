# coding=utf-8
__author__ = 'wulei'
from django.core.management.base import BaseCommand

import datetime
from flashsale.pay.models import Customer
from django.conf import settings
from django.contrib.auth.models import User
from flashsale.pay.models import SaleOrder, SaleRefund

class Command(BaseCommand):
    def handle(self, *args, **options):
        df = datetime.datetime(2016, 5, 15, 23, 59, 59)
        sale_order_list = SaleOrder.objects.filter(pay_time__lte=df, status__in=(SaleOrder.TRADE_NO_CREATE_PAY,
                                                                                 SaleOrder.WAIT_BUYER_PAY,
                                                                                 SaleOrder.WAIT_SELLER_SEND_GOODS,
                                                                                 SaleOrder.WAIT_BUYER_CONFIRM_GOODS,
                                                                                 SaleOrder.TRADE_BUYER_SIGNED));
        # TRADE_NO_CREATE_PAY = 0
        # WAIT_BUYER_PAY = 1
        # WAIT_SELLER_SEND_GOODS = 2
        # WAIT_BUYER_CONFIRM_GOODS = 3
        # TRADE_BUYER_SIGNED = 4
        # TRADE_FINISHED = 5
        # TRADE_CLOSED = 6
        # TRADE_CLOSED_BY_SYS = 7

        # NO_REFUND = 0
        # REFUND_CLOSED = 1
        # REFUND_REFUSE_BUYER = 2
        # REFUND_WAIT_SELLER_AGREE = 3
        # REFUND_WAIT_RETURN_GOODS = 4
        # REFUND_CONFIRM_GOODS = 5
        # REFUND_APPROVE = 6
        # REFUND_SUCCESS = 7
        print sale_order_list.count()
        num = 0
        for order in sale_order_list:
            if order.status in [SaleOrder.TRADE_NO_CREATE_PAY, SaleOrder.WAIT_BUYER_PAY ]:
                order.status = SaleOrder.TRADE_CLOSED_BY_SYS
                order.refund_status = SaleRefund.NO_REFUND
                order.save()
                num = num + 1
            elif order.status in [SaleOrder.WAIT_SELLER_SEND_GOODS]:
                num = num + 1
            elif order.status in [SaleOrder.WAIT_BUYER_CONFIRM_GOODS,SaleOrder.TRADE_BUYER_SIGNED]:
                if order.refund_status != SaleRefund.NO_REFUND:
                    order.status = SaleOrder.TRADE_CLOSED
                    order.refund_status = SaleRefund.REFUND_SUCCESS
                else:
                    order.status = SaleOrder.TRADE_FINISHED
                order.save()
                num = num + 1
            else:
                if order.refund_status not in [SaleRefund.NO_REFUND, SaleRefund.REFUND_CLOSED, SaleRefund.REFUND_SUCCESS ]:
                    order.refund_status = SaleRefund.REFUND_CLOSED
                    order.save()
                    num = num + 1
        print num
