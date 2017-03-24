# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from supplychain.supplier.models import SaleSupplier

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """ usage: python manage.py update_supplier_vendorcode """

    def handle(self, *args, **options):

        suppliers = SaleSupplier.objects.only('id', 'vendor_code')
        start = 0
        for supplier in suppliers.iterator():
            start += 1
            if not supplier.vendor_code:
                supplier.vendor_code = SaleSupplier.gen_vendor_code(start)
                supplier.save(update_fields=['vendor_code'])
            if start % 1000 == 0:
                print 'count=', start

