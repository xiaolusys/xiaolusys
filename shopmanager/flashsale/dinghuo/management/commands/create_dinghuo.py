# coding: utf-8
import datetime
from operator import itemgetter
from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Max, Sum

from core.options import log_action, ADDITION, CHANGE
from flashsale.dinghuo.models import OrderDetail, OrderList
from shopback import paramconfig as pcfg
from shopback.items.models import Product, ProductSku
from shopback.trades.models import (MergeOrder, TRADE_TYPE, SYS_TRADE_STATUS)
from supplychain.supplier.models import SaleProduct, SupplierCharge, SaleSupplier


ADMIN_ID = 1

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-d', '--delete', dest='is_del', action='store_true', default=False),
    )

    @classmethod
    def delete_orderlist(cls):
        OrderList.objects.filter(created_by=OrderList.CREATED_BY_MACHINE).delete()

    def handle(self, *args, **kwargs):
        from flashsale.dinghuo.tasks import create_dinghuo

        is_del = kwargs['is_del']

        if is_del:
            self.delete_orderlist()
        else:
            create_dinghuo()
