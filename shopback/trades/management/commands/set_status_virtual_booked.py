# coding=utf-8

from django.core.management.base import BaseCommand
import json
from shopback.trades.models import PackageSkuItem

from shopback.dinghuo.models.purchase_order import OrderList
from django.conf import settings
from django.contrib.auth.models import User

##用法 python manage.py set_status_virtual_booked -id 123 -unikey 1232
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-id', '--packageskuitem_id', action='store', dest='packageskuitem_id',
            type=str,
        )

        parser.add_argument(
            '-unikey', '--purchase_order_unikey', action='store', dest='purchase_order_unikey',
            type=str,
        )

    def handle(self, *args, **options):
        id = options.get("packageskuitem_id")
        purchase_order_unikey = options.get('purchase_order_unikey')
        print id,purchase_order_unikey
        PackageSkuItem.objects.filter(id=id).first().set_status_virtual_booked(purchase_order_unikey)