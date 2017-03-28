# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime, time
from django.test import TestCase, tag

from flashsale.pay.models import SaleTrade, SaleOrder, SaleRefund
from ..adapter.mall.push import order
from ..adapter.ware.pull import oms
from shopback.trades.models import PackageOrder


class OMSTestCase(TestCase):

    fixtures = [
        'test.outware.base.json',
        'test.outware.salesupplier.json',
        'test.outware.product.json',
        # 'test.outware.purchase.json',
        'test.outware.order.json',
    ]

    def setUp(self):
        pass

    @tag('C')
    def testCreateAndCancelWareOrder(self):
        # user the following test
        sale_trade = SaleTrade.objects.first()
        sale_trade.tid = SaleTrade.gen_unikey()
        resp = order.push_outware_order_by_sale_trade(sale_trade)
        self.assertTrue(resp['success'])

        resp = oms.cancel_order(sale_trade.tid)
        self.assertTrue(resp['success'])

    @tag('C')
    def testCreateAndCancelWarePackage(self):
        package_order = PackageOrder.objects.first()
        package_order.pid = '%s'%(time.time())
        resp = order.push_outware_order_by_package(package_order)
        self.assertTrue(resp['success'])

        resp = oms.cancel_order(package_order.pid)
        self.assertTrue(resp['success'])


class SlycTestCase(TestCase):

    fixtures = [
        'test.outware.base.json',
        'test.outware.slyc.json'
    ]

    def setUp(self):
        pass

    @tag('C')
    def testCreateAndCancelWareOrder(self):
        sale_trade = SaleTrade.objects.first()
        sale_trade.tid = SaleTrade.gen_unikey()
        resp = order.push_outware_order_by_sale_trade(sale_trade)
        self.assertTrue(resp['success'])

        resp = oms.cancel_order(sale_trade.tid)
        self.assertTrue(resp['success'])

class OMSRefundTestCase(TestCase):
    # TODO@MERON 退款单创建不能自动测试, 只能手动修改测试
    # fixtures = [
    #     'test.outware.base.json',
    #     'test.outware.salesupplier.json',
    #     'test.outware.product.json',
    #     'test.outware.order.json',
    #     'test.outware.refund.json',
    # ]

    #　
    def createRefundInbound(self):
        sale_refund = SaleRefund.objects.first()
        resp = order.push_outware_inbound_by_sale_refund(sale_refund)
        self.assertTrue(resp['success'])



