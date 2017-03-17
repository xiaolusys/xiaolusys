# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime, time
from django.test import TestCase

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

    def testInboundOrderConfirm(self):
        data = {
            'order_code': 'fid201702055896d6ecf0f66',
            'store_code': 'SZWH01',
            'order_type': 601,
            'inbound_skus': [{
                'sku_code': 'SP111111AA',
                'batch_no': 'AJEV',
                'pull_good_qty': 2,
                'pull_bad_qty': 1,
                'object': 'OutwareInboundSku',
            }],
            'object': 'OutwareInboundOrder',
        }

        order_code = data['order_code']
        pms.update_outware_inbound_by_po_confirm(order_code, data['order_type'], DictObject().fresh_form_data(data))

        ow_inbound = OutwareInboundOrder.objects.get(inbound_code=order_code, order_type=data['order_type'])
        self.assertEqual(ow_inbound.status, constants.ARRIVED)
        self.assertEqual(ow_inbound.store_code, data['store_code'])

        for sku in data['inbound_skus']:
            ow_stock = OutwareSkuStock.objects.get(sku_code=sku['sku_code'])
            self.assertEqual(ow_stock.pull_good_available_qty, sku['pull_good_qty'])
            self.assertEqual(ow_stock.pull_bad_qty, sku['pull_bad_qty'])


    def testRefundOrderConfirm(self):
        data = {
            'order_code': 'rf170208589abe94959ae',
            'store_code': 'SZWH01',
            'order_type': 501,
            'inbound_skus': [{
                'sku_code': 'SP111111AA',
                'batch_no': 'AJEV',
                'pull_good_qty': 1,
                'pull_bad_qty': 1,
                'object': 'OutwareInboundSku',
            }],
            'object': 'OutwareInboundOrder',
        }

        order_code = data['order_code']
        pms.update_outware_inbound_by_po_confirm(order_code, data['order_type'], DictObject().fresh_form_data(data))

        ow_inbound = OutwareInboundOrder.objects.get(inbound_code=order_code, order_type=data['order_type'])
        self.assertEqual(ow_inbound.status, constants.ARRIVED)
        self.assertEqual(ow_inbound.store_code, data['store_code'])

        for sku in data['inbound_skus']:
            ow_stock = OutwareSkuStock.objects.get(sku_code=sku['sku_code'])
            self.assertEqual(ow_stock.pull_good_available_qty, sku['pull_good_qty'])
            self.assertEqual(ow_stock.pull_bad_qty, sku['pull_bad_qty'])


    def testOrderDeliver(self):
        data = {
            'order_code': 'xd16111358284ace3a74f',
            'order_type': 401,
            'packages': [{
                'store_code': 'SZWH01',
                'logistics_no': '9867542222',
                'carrier_code': 'YUNDA',
                'package_items': [{
                    'sku_code': 'SP111111AA',
                    'batch_no': 'AJEV',
                    'sku_qty': 2,
                    'object': 'OutwarePackageSku',
                }],
                'object': 'OutwarePackage',
            }],
            'object': 'OutwareObject',
        }

        order_code = data['order_code']
        oms.update_outware_order_by_order_delivery(order_code, data['order_type'], DictObject().fresh_form_data(data))

        for package in data['packages']:
            ow_packages = OutwarePackage.objects.get(
                package_order_code=order_code, logistics_no=package['logistics_no'], carrier_code=package['carrier_code'])
            self.assertEqual(ow_packages.store_code, package['store_code'])



