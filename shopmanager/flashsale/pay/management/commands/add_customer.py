# coding=utf-8
__author__ = 'jishu_linjie'
from django.core.management.base import BaseCommand

from flashsale.pay.models import Customer
from django.conf import settings
from django.contrib.auth.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        if not settings.DEBUG:
            return
        user = User.objects.get(username='shanwei.zhao')
        Customer.objects.get_or_create(user=user)

