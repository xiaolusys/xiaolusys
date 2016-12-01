# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.dispatch import receiver
from signals import signal_charge_success, signal_refund_success

from .models import SaleTrade
from .tasks import confirmTradeChargeTask, notifyTradeRefundTask

@receiver(signal_charge_success)
def confirm_paid_and_update_saletrade_status(sender, message, **kwargs):

    data = message['data']
    charge = data['id']
    order_no = data['order_no']
    charge_time = data['time_paid']

    strade = SaleTrade.objects.get(tid=order_no)
    confirmTradeChargeTask.delay(strade.id, charge_time=charge_time, charge=charge)


@receiver(signal_refund_success)
def confirm_refunded_and_update_salerefund_status(sender, message, **kwargs):

    data = message['data']
    notifyTradeRefundTask.delay(data)