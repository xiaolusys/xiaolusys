# coding=utf-8
from __future__ import unicode_literals, absolute_import
import json
from django.test import TestCase
from flashsale.coupon.models import UserCoupon, CouponTransferRecord, TransferCouponDetail

import logging

logger = logging.getLogger(__name__)


class CouponTransferRecordTestCase(TestCase):
    fixtures = [
        "test.flashsale.coupon.transferrecord.json",
        "test.flashsale.coupon.customer.json",
        'test.flashsale.coupon.usercoupon.json',
        'test.flashsale.xiaolumm.referalrelationship.json',
    ]

    transfer_coupon = '/rest/v2/trancoupon/50/transfer_coupon'  # 直接转券

    def setUp(self):
        self.username = 'xiaolu'
        self.password = 'test'
        self.client.login(username=self.username, password=self.password)

    def testTransferCoupons(self):
        """测试 妈妈id 44 转券 给 妈妈id 25839
        """
        response = self.client.post(self.transfer_coupon, {}, ACCEPT='application/json; q=0.01')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        r = CouponTransferRecord.objects.get(id=50)
        self.assertEqual(r.transfer_status, CouponTransferRecord.DELIVERED)
        coupon = UserCoupon.objects.get(id=866636)
        self.assertEqual(coupon.customer_id, 9)
        self.assertEqual(coupon.extras['chain'], [44])
        c = TransferCouponDetail.objects.filter(transfer_id=50, coupon_id=866636).count()
        self.assertEqual(c, 1)
        self.assertEqual(data['code'], 0)
