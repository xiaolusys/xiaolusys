# coding: utf8
from __future__ import absolute_import, unicode_literals

import json
import datetime, time
from django.test import TestCase, tag
from django.core.urlresolvers import reverse

from ..models import OutwareInboundOrder, OutwareSkuStock, OutwarePackage
from ..adapter.ware.push import oms, pms
from core.apis.models import DictObject
from .. import constants

class CallbackTestCase(TestCase):

    fixtures = [
        'test.outware.base.json',
        'test.outware.salesupplier.json',
        'test.outware.product.json',
        'test.outware.purchase.json',
        'test.outware.order.json',
        'test.outware.callback.json',
    ]

    def setUp(self):
        pass

    @tag('B')
    def testInboundPoConfirmCallback(self):
        data = {
            u'sign_type': u'md5',
            u'data': json.dumps({
                "order_code":"fid201702055896d6ecf0f66",
                "order_type":"purchase",
                "store_code":"SZWH01",
                "warehouse_warrant_items":[
                    {
                        "available_qty":3,
                        "bad_qty":0,
                        "batch_no":" ",
                        "sku_id":"SP111111AA",
                        "sku_name":"vivo X9Plus手机红色红色"
                    }
                ]
            }),
            u'app_id': u'app20170308hnabcpls',
            u'sign': u'3ce74515fbf010e049c428d09ae18e64'}

        response = self.client.post(
            reverse('honeycomb:callback-po-confirm'),
            data,
            ACCPET='application/json;'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 0)

    @tag('B')
    def testInboundOrderOrderStateCallback(self):
        data = {
            u'sign_type': u'md5',
            u'data': u'{"order_number":"xd16111358284ace3a74f","status":26,"status_display":"开始拣货"}',
            u'app_id': u'app20170308hnabcpls',
            u'sign': u'1fae0f15b89a12ae66cebb59ff6756a0'}

        response = self.client.post(
            reverse('honeycomb:callback-order-state'),
            data,
            ACCPET='application/json;'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 0)

    @tag('B')
    def testInboundOrderGoodlackCallback(self):
        data = {
            u'sign_type': u'md5',
            u'data': json.dumps({
                "order_number":"xd16111358284ace3a74f",
                "order_type": constants.ORDER_LACKGOOD['code'],
                "lack_goods":[
                    {
                        "sku_code":"SP11111AAA",
                        "sku_name":"ABCD",
                        "lack_qty":2
                    }
                ]
            }),
            u'app_id': u'app20170308hnabcpls',
            u'sign': u'4654cf0964d947d322e69dc000e6282e'
        }

        response = self.client.post(
            reverse('honeycomb:callback-order-goodlack'),
            data,
            ACCPET='application/json;'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 0)

    @tag('B')
    def testInboundOrderDeliveryCallback(self):
        data = {
            u'sign_type': u'md5',
            u'data': json.dumps({
                "order_code": "166271",
                "order_type": 'user_pack',
                "packages": [{
                    "whse_code": "SZWH01",
                    "logistics_no": "9867542222",
                    "carrier_code": "YUNDA",
                    "package_items": [{
                        "sku_id": "SP111111AA",
                        "batch_no": "AJEV",
                        "send_qty": 2
                    }]
                }]
            }),
            u'app_id': u'app20170308hnabcpls',
            u'sign': u'b904623bcbb0b59d089a42892246e855'}

        response = self.client.post(
            reverse('honeycomb:callback-order-delivery'),
            data,
            ACCPET='application/json;'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 0)

