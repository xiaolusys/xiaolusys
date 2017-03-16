# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime, time
from django.test import TestCase

from supplychain.supplier.models import SaleSupplier, SaleProduct
from shopback.items.models import Product, ProductSku
from ..adapter.mall.push import supplier, product, inbound
from flashsale.forecast.models import ForecastInbound

class PMSTestCase(TestCase):

    fixtures = [
        'test.outware.base.json',
        'test.outware.salesupplier.json',
        'test.outware.product.json',
        'test.outware.purchase.json',
        'test.outware.order.json',
    ]

    def setUp(self):
        pass

    def setForSupplierAndSku(self):
        sale_supplier = SaleSupplier.objects.first()
        sale_supplier.vendor_code = 'lxh%s' % (int(time.time()))
        sale_supplier.supplier_name = '来享汇%s' % (int(time.time()))
        sale_supplier.save()

        skus = ProductSku.objects.all()
        for sku in skus:
            sku.outer_id = 'STU%s' % int(time.time() * 1000)
            sku.supplier_skucode = '%s' % int(time.time() * 1000)
            sku.save()

    def createSupplier(self):
        sale_supplier = SaleSupplier.objects.first()
        resp = supplier.push_ware_supplier_by_mall_supplier(sale_supplier)
        self.assertTrue(resp['success'])

    def testCreateProductsku(self):
        self.setForSupplierAndSku()
        self.createSupplier()

        sale_product = SaleProduct.objects.first()
        resp = product.push_ware_sku_by_saleproduct(sale_product)
        self.assertGreater(len(resp), 0)

    def testWareInbound(self):
        forestib = ForecastInbound.objects.first()
        resp = inbound.push_outware_inbound_by_forecast_order(forestib)
        self.assertTrue(resp['success'])




