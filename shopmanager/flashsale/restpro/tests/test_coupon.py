# coding=utf-8
import json
from django.test import TestCase


class UserCouponTestCase(TestCase):
    fixtures = ["test.flashsale.coupon.conponpool.json",
                "test.flashsale.coupon.coupontemplate.json",
                "test.flashsale.coupon.customer.json",
                "test.flashsale.coupon.usercoupon.json"]

    def setUp(self):
        self.username = 'jie.lin'
        self.password = 'linjie123'
        self.client.login(username=self.username, password=self.password)

    def testUserCoupons(self):
        response = self.client.get('/rest/v1/usercoupons', {},
                                   ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        print "data:", data

