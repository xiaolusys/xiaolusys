# coding=utf-8
__author__ = 'jishu_linjie'
from django.core.management.base import BaseCommand
from flashsale.promotion.views_handler import close_saleorder_by_obsolete_awards


class Command(BaseCommand):
    def handle(self, *args, **options):
        close_saleorder_by_obsolete_awards()


