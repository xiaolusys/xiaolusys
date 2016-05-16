# coding: utf-8

import datetime

from django.core.management.base import BaseCommand

from flashsale.dinghuo.models import OrderList


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        from flashsale.dinghuo.tasks import get_suppliers, create_orderlist

        OrderList.objects.filter(created__gte=datetime.datetime(2016, 5, 16).date()).delete()
        for supplier in get_suppliers(datetime.datetime(2016, 5, 15, 10, 15)):
            create_orderlist(supplier)
