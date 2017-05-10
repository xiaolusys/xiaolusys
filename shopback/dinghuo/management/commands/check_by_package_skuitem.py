# coding=utf-8

from django.core.management.base import BaseCommand

from shopback.dinghuo.models.purchase_order import OrderList
from django.conf import settings
from django.contrib.auth.models import User


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-id', '--order_list_id', action='store', dest='order_list_id',
            type=int,
        )

    def handle(self, *args, **options):
        id = options.get('order_list_id')
        ol = OrderList.objects.filter(id=id).first()
        ol.check_by_package_skuitem()