# coding=utf-8
__author__ = 'jishu_linjie'
from django.core.management.base import BaseCommand
from django.conf import settings
from flashsale.pay.tasks import task_release_coupon_push


class Command(BaseCommand):
    def handle(self, *args, **options):
        if not settings.DEBUG:
            return
        task_release_coupon_push.s(1).delay()

