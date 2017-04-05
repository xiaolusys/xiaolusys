# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.test import TestCase
import random
import datetime
from ..apis.v1 import Charge

def random_string():
    return ''.join(random.sample(list('abcdefghijklmnopqrstuvwxyz0123456789'),8))

class XiaoluPayChargeTestCase(TestCase):
    fixtures = [ ]

    def setUp(self):
        self.order_no = 'xt%s%s'%(datetime.datetime.now().strftime('%Y%m%d%H%M'), random_string())
        self.data = {
            'order_no': self.order_no,
            'amount': 20,
            'channel': '',
            'currency': 'cny',
            'subject': 'test idea',
            'body': '',
            'extra': {},
        }

    def test_wx_pub_charge(self):
        channel = 'wx_pub'
        data = self.data.copy()
        data['channel'] = channel
        data['extra'] = {
            'open_id': 'our5huIOSuFF5FdojFMFNP5HNOmA'
        }
        ch = Charge.create(**data)
        self.assertEqual(ch.order_no, self.order_no)
        self.assertEqual(ch.channel, channel)
        self.assertEqual(ch.extra['open_id'], data['extra']['open_id'])

    def test_wx_charge(self):
        channel = 'wx'
        data = self.data.copy()
        data['channel'] = channel
        ch = Charge.create(**data)
        self.assertEqual(ch.order_no, self.order_no)
        self.assertEqual(ch.channel, channel)

    def test_alipay_charge(self):
        channel = 'alipay'
        data = self.data.copy()
        data['channel'] = channel
        ch = Charge.create(**data)
        self.assertEqual(ch.order_no, self.order_no)
        self.assertEqual(ch.channel, channel)

    def test_alipay_wap_charge(self):
        channel = 'alipay_wap'
        data = self.data.copy()
        data['channel'] = channel
        data['extra'] = {
            "cancel_url": "https://i.xiaolumm.com/mall/ol.html?type=1",
            "success_url": "https://i.xiaolumm.com/mall/order/success/"
        }
        ch = Charge.create(**data)
        self.assertEqual(ch.order_no, self.order_no)
        self.assertEqual(ch.channel, channel)
        self.assertEqual(ch.extra, data['extra'])

    def test_wx_querytrade(self):
        data = self.data.copy()
        data['channel'] = 'wx'
        Charge.create(**data)
        order = Charge.retrieve(data['order_no'])
        self.assertEqual(order.paid, False)
        self.assertEqual(order.order_no, data['order_no'])
        self.assertEqual(order.channel, data['channel'])