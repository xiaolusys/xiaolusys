# coding: utf-8

from optparse import make_option
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-s', '--skuid', dest='sku_id', action='store', help='SkuId'),
    )

    def handle(self, *args, **kwargs):
        from flashsale.pay.tasks import task_update_orderlist

        sku_id = kwargs.get('sku_id')
        if not sku_id:
            return

        task_update_orderlist(sku_id)
