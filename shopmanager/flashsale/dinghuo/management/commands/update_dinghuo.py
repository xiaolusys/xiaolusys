# coding: utf-8
import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from flashsale.dinghuo.models import OrderList

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        threshold = datetime.date(2016, 1, 1)
        print OrderList.objects.filter(created__lte=threshold).exclude(status=OrderList.COMPLETED).update(status=OrderList.COMPLETED)
