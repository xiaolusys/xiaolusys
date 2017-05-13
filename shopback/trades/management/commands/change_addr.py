# coding=utf-8

from django.core.management.base import BaseCommand
import json
from shopback.trades.models import PackageSkuItem,PackageOrder
import collections
from flashsale.pay.models import SaleTrade

#用法  python manage.py change_addr -addr 江苏省,无锡市,会山区,桥东321号,邓辉22,15800972458 -pid 185634 -id 597448
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-addr', '--address', action='store', dest='address',
            type=str,
        )
        parser.add_argument(
            '-pid', '--package_order_pid', action='store', dest='package_order_pid',
            type=str,
        )
        parser.add_argument(
            '-id', '--sale_trade_id', action='store', dest='sale_trade_id',
            type=str,
        )
    def handle(self, *args, **options):
        addr = options.get("address")
        package_order_pid = options.get('package_order_pid')
        sale_trade_id = options.get('sale_trade_id')
        print addr.split(',')
        addr_template = ['receiver_state','receiver_city', 'receiver_district',  'receiver_address', 'receiver_name','receiver_mobile']
        addr_dict = dict(zip(addr_template,addr.split(',')))
        PackageOrder.objects.filter(pid=package_order_pid).update(**addr_dict)
        SaleTrade.objects.filter(id=sale_trade_id).update(**addr_dict)

