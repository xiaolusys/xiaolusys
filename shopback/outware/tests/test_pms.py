# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime, time
from django.test import TestCase, tag

from pms.supplier.models import SaleSupplier, SaleProduct
from shopback.items.models import Product, ProductSku
from ..adapter.mall.push import supplier, product, inbound
from ..adapter.ware.pull import pms
from .. import constants
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

    @tag('B')
    def testCreateSupplier(self):
        self.setForSupplierAndSku()
        sale_supplier = SaleSupplier.objects.first()
        resp = supplier.push_ware_supplier_by_mall_supplier(sale_supplier)
        self.assertTrue(resp['success'])

    @tag('B')
    def createProductsku(self):
        # 该接口暂不做测试，由于蜂巢方面商品资料信息录入与响应属于异步操作
        self.setForSupplierAndSku()
        self.testCreateSupplier()
        # create productsku
        sale_product = SaleProduct.objects.first()
        resp = product.push_ware_sku_by_saleproduct(sale_product)
        self.assertGreater(len(resp), 0)

        # recreat productsku ,不能马上执行,蜂巢不能及时更新sku资料
        # resp = product.push_ware_sku_by_saleproduct(sale_product)
        # self.assertGreater(len(resp), 0)

    @tag('B')
    def testCreateAndCancelPurchaseInbound(self):
        forestib = ForecastInbound.objects.first()
        resp = inbound.push_outware_inbound_by_forecast_order(forestib)
        self.assertTrue(resp['success'])

        # resp = pms.cancel_inbound_order(
        #     forestib.forecast_no ,
        #     forestib.supplier.vendor_code,
        #     constants.ORDER_PURCHASE['code'])
        # self.assertTrue(resp['success'])



