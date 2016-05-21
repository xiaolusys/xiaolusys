# coding: utf-8

import json
from django.test import TestCase

from flashsale.dinghuo.models import InBound, InBoundDetail, OrderList, OrderDetail


class InBoundTestCase(TestCase):
    fixtures = [
        'test.inbound.user.json', 'test.inbound.supplier.json',
        'test.inbound.productcategory.json', 'test.inbound.product.json',
        'test.inbound.productsku.json', 'test.inbound.orderlist.json',
        'test.inbound.orderdetail.json'
    ]

    create_inbound_data = {
        '162264': {
            'product_id': 40243,
            'sku_id': 162264,
            'arrival_quantity': 6
        }
    }

    def setUp(self):
        self.username = 'enjun.wang'
        self.password = 'enjun.wang2015'
        self.client.login(username=self.username, password=self.password)

    def test_create(self):
        r = self.client.post('/sale/dinghuo/inbound/create_inbound',
                             {'inbound_skus':
                              json.dumps(self.create_inbound_data),
                              'memo': '',
                              'supplier_id': 28712},
                             ACCPET='application/json')
        self.assertEqual(r.status_code, 200)
        result = json.loads(r.content)
        self.assertIn('inbound', result)
        self.assertGreater(result['inbound']['id'], 0)
