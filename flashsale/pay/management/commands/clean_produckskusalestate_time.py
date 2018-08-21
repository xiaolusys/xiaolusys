# coding: utf8
from __future__ import absolute_import, unicode_literals

from datetime import datetime
from django.core.management.base import BaseCommand
from django.db.models import Min

from shopback.items.models import ProductSkuSaleStats

class Command(BaseCommand):
    def handle(self, *args, **options):

        sale_stats = ProductSkuSaleStats.objects.filter(
            sale_start_time__isnull=True,
            sale_end_time__isnull=True,
        )
        print 'time null count:', sale_stats.count()
        for stat in sale_stats.iterator():
            mp = stat.product.get_product_model()
            stat.sale_start_time = mp.onshelf_time
            stat.sale_end_time   = mp.offshelf_time
            stat.save(update_fields=['sale_start_time', 'sale_end_time'])
            print stat.sku.outer_id, stat.get_status_display(), mp.get_shelf_status_display(), stat.sale_start_time, stat.sale_end_time

