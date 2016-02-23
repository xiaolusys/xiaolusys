# coding: utf-8
import datetime
import re

from django.core.management.base import BaseCommand

from shopback.items.models import Product
from shopback.categorys.models import ProductCategory


class Command(BaseCommand):
    DIGITS_PATTERN = re.compile('^\d+$')

    def handle(self, *args, **kwargs):
        level_2_ids = []
        level_3_ids = []
        for category in ProductCategory.objects.filter(parent_cid=4,
                                                       status='normal'):
            level_2_ids.append(category.cid)
        for category in ProductCategory.objects.filter(parent_cid__in=level_2_ids,
                                                       status='normal'):
            level_3_ids.append(category.cid)
        for product in Product.objects.filter(
                status='normal',
                category_id__in=level_2_ids + level_3_ids,
                created__gte=datetime.datetime.now() - datetime.timedelta(days=30)):
            print product.id
            count = 0
            for sku in product.prod_skus.filter(status='normal').order_by('id'):
                count += 1
                if sku.barcode:
                    continue
                if self.DIGITS_PATTERN.match(sku.barcode.strip()):
                    continue
                sku.barcode = '%s%d' % (product.outer_id, count)
                sku.save()
