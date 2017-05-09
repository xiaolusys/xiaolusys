# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from pms.supplier.models import SaleProduct, SaleSupplier
from flashsale.pay.models import ModelProduct
from shopback.items.models import SkuStock, Product, ProductSku

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """ usage: python manage.py migrate_salecategory [cat_fid] [cat_tid] """
    def add_arguments(self, parser):
        # Positional arguments
        # parser.add_argument('cat_fid', nargs='+', type=int, help='from category_id')
        pass

    def handle(self, *args, **options):

        mp_stocking_list = []
        mps = ModelProduct.objects.filter(shelf_status=ModelProduct.ON_SHELF)
        for mp in mps.iterator():
            saleproduct = mp.sale_product
            supplier = saleproduct.sale_supplier
            mp_stock = {
                'id': mp.id,
                'stock_num': 0,
                'name': mp.name,
                'supplier_id':   supplier.id,
                'supplier_name': supplier.supplier_name,
                'stocking_mode': supplier.stocking_mode,
            }
            for product in mp.products:
                sku_stocks = SkuStock.objects.filter(product=product, status=0)
                for sto in sku_stocks.iterator():
                    mp_stock['stock_num'] += sto.realtime_quantity

            mp_stocking_list.append(mp_stock)

        print '================count:', len(mp_stocking_list)
        for mp in mp_stocking_list:
            if mp['stock_num'] > 0 and mp['stocking_mode'] == 0:
                print ':'.join([str(mp['id']), mp['name'], mp['supplier_name'], str(mp['stock_num'])])

