# coding=utf-8

from django.core.management.base import BaseCommand
import json
from shopback.trades.models import PackageSkuItem
from flashsale.pay.models import SaleOrder

from shopback.dinghuo.models.purchase_order import OrderList
from django.conf import settings
from django.contrib.auth.models import User


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-id', '--saleorder_id', action='store', dest='saleorder_id',
            type=str,
        )

    def handle(self, *args, **options):
        id = options.get("saleorder_id")
        ids = json.loads(id)
        print ids
        SaleOrder.objects.filter(id__in=ids).update(status=3)