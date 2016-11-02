# coding=utf-8
__author__ = 'meron'
from django.core.management.base import BaseCommand

from supplychain.supplier.models import SaleProduct
from supplychain.supplier.models import SaleSupplier
from flashsale.pay.models import ModelProduct

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """ usage: python manage.py migrate_salecategory [cat_fid] [cat_tid] """
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('cat_fid', nargs='+', type=int, help='from category_id')
        parser.add_argument('cat_tid', nargs='+', type=int, help='to category_id')

    def handle(self, *args, **options):

        cat_fid = options.get('cat_fid')
        cat_tid = options.get('cat_tid')
        if len(cat_fid) != 1 or len(cat_tid) != 1:
            print 'usage: python manage.py migrate_salecategory [cat_fid] [cat_tid], but %s, %s give'%(cat_fid, cat_tid)
            return
        cat_fid = cat_fid[0]
        cat_tid = cat_tid[0]
        saleproducts = SaleProduct.objects.filter(sale_category_id=cat_fid)
        logger.info('migrate saleproduct count:%s'% saleproducts.count())
        saleproducts.update(sale_category_id=cat_tid)

        salesuppliers = SaleSupplier.objects.filter(category_id=cat_fid)
        logger.info('migrate salesupplier count:%s' % salesuppliers.count())
        salesuppliers.update(category_id=cat_tid)

        modelproducts = ModelProduct.objects.filter(salecategory_id=cat_fid)
        logger.info('migrate modelproduct count:%s' % modelproducts.count())
        modelproducts.update(salecategory_id=cat_tid)