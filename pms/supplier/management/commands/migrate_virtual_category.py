# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from pms.supplier.models import SaleCategory, SaleProduct
from flashsale.pay.models import ModelProduct

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """ usage: python manage.py migrate_salecategory [cat_fid] [cat_tid]

    """
    # def add_arguments(self, parser):
    #     # Positional arguments
    #     parser.add_argument('cat_fid', nargs='+', type=int, help='from category_id')
    #     parser.add_argument('cat_tid', nargs='+', type=int, help='to category_id')

    category_maps = {
        '8': 149,
        '7': 150,
        '5': 151,
        '3': 152,
    }

    def handle(self, *args, **options):
        mps = ModelProduct.objects.filter(product_type=1)
        for mp in mps:
            new_cat_id   = self.category_maps.get(mp.salecategory.cid.split('-')[0])
            new_category = SaleCategory.objects.get(id=new_cat_id)
            mp.salecategory = new_category
            mp.save()

            saleproduct = mp.saleproduct
            saleproduct.sale_category = new_category
            saleproduct.save()
            print mp.id