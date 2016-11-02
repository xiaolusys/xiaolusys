# coding=utf-8
__author__ = 'meron'
from django.core.management.base import BaseCommand

from flashsale.pay.models import SaleTrade, SaleOrder
import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, *args, **options):
        sorder_buyers = SaleOrder.objects.values_list('id','sale_trade__buyer_id')
        cnt = 0
        for order_id, buyer_id in sorder_buyers:
            SaleOrder.objects.filter(id=order_id).update(buyer_id=buyer_id)
            cnt += 1
            if cnt % 5000 == 0:
                print 'execute: ', cnt
