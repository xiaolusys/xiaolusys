# coding=utf-8
__author__ = 'jishu_linjie'
from django.core.management.base import BaseCommand, CommandError
from django.core import management

from flashsale.pay.models import SaleTrade
from flashsale.pay.signals import signal_saletrade_pay_confirm
from django.conf import settings


class Command(BaseCommand):
    def handle(self, *args, **options):
        if not settings.DEBUG:
            return
        st = SaleTrade.objects.get(id=642, buyer_id=1)
        print '找到订单%s', st
        print '发送付款成功信号'
        signal_saletrade_pay_confirm.send(sender=SaleTrade, obj=st)
