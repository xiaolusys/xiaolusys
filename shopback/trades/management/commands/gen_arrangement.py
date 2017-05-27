# coding=utf-8

from django.core.management.base import BaseCommand
import json
from shopback.trades.models import PackageSkuItem

from shopback.dinghuo.models.purchase_order import OrderList
from django.conf import settings
from django.contrib.auth.models import User


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '-id', '--packageskuitem_id', action='store', dest='packageskuitem_id',
            type=str,
        )

    def handle(self, *args, **options):
        id = options.get("packageskuitem_id")
        PackageSkuItem.objects.filter(id=id).first().gen_arrangement()
