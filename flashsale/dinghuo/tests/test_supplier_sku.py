# coding=utf-8
from flashsale.dinghuo.models import OrderDetail,OrderList
from supplychain.supplier.models import  SaleSupplier
import json
from django.test import TestCase

# import os
# import sys
# import django
# sys.path.append("/home/fpcnm/myProjects/xiaoluMM4/xiaolusys/shopmanager/")
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")
# django.setup()

class SupplierSkuTest(TestCase):
    fixtures = [


        "test.supplier_sku_customer.json",
        # "test.supplier_sku.salecategory.json"
        "test.supplier_sku.salesupplier.json",
        "test.supplier_sku.orderlist.json",
        "test.supplier_sku.orderdetail.json"
    ]

    def setUp(self):
        self.username = '13739234188'
        self.password = '123456'
        self.client.login(username=self.username, password=self.password)

    def test_get_supplier_sku(self):
        # SaleSupplier.objects.get(id=29463)
        print "nimb"


