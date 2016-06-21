# coding=utf-8
__author__ = 'wulei'
from django.core.management.base import BaseCommand

from flashsale.pay.models import Customer
from django.conf import settings
from django.contrib.auth.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        sale_order_list = SaleOrder.objects.all();
