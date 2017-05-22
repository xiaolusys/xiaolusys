# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.test import TestCase, tag
import time
from ..apis.v1.transfers import Transfer

class XiaoluPayTransferTestCase(TestCase):

    def setUp(self):
        self.data = {
            'order_code': int(time.time()),
            'channel': 'sandpay',
            'amount': 10,
            'desc': '',
            'mch_id': '17057042',
            'time_out': 24 * 60 * 60,
            'extras': {
                'accNo': '6216261000000000018',
                'accName': '全渠道',
                'payMode': 1,
                'channelType': '07'
            },
        }

    @tag('C')
    def test_transfer_create(self):
        tr = Transfer.create(**self.data)
        self.assertEqual(tr.order_code, self.data['order_code'])
        self.assertEqual(tr.channel, self.data['channel'])


    @tag('C')
    def test_transfer_retrieve(self):
        tr = Transfer.retrieve(self.data['order_code'])
        self.assertEqual(tr.order_code, self.data['order_code'])
        self.assertEqual(tr.channel, self.data['channel'])