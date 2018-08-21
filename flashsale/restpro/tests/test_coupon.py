# coding=utf-8
import json
from django.test import TestCase
from flashsale.coupon.models import UserCoupon, OrderShareCoupon


class UserCouponTestCase(TestCase):
    fixtures = [
        "test.flashsale.coupon.tmpsharecoupon.json",
        "test.flashsale.coupon.ordersharecoupon.json",
        "test.flashsale.coupon.coupontemplate.json",
        "test.flashsale.coupon.customer.json",
        "test.flashsale.coupon.usercoupon.json",
        "test.flashsale.coupon.product.json",
        "test.flashsale.coupon.productcategory.json",
        "test.flashsale.coupon.shoppingcart.json",
    ]
    url_user_coupons = '/rest/v2/usercoupons'  # 用户优惠券
    url_user_past_coupons = '/rest/v2/usercoupons/list_past_coupon'  # 用户过期优惠券
    url_usercoupons_by_template = '/rest/v2/usercoupons/get_usercoupons_by_template'  # 通过模板id获取优惠券
    url_choose_coupon = '/rest/v2/usercoupons/{0}/choose_coupon'

    def setUp(self):
        self.username = '13739234188'
        self.password = '123456'
        self.client.login(username=self.username, password=self.password)

    def testUserUnusedCoupons(self):
        response = self.client.get(self.url_user_coupons, {}, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        results = data['results']
        for user_coupon in results:
            self.assertEqual(user_coupon['status'], UserCoupon.UNUSED)

    def testUserPastCoupons(self):
        response = self.client.get(self.url_user_past_coupons, {}, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        results = data['results']
        for user_coupon in results:
            self.assertEqual(user_coupon['status'], UserCoupon.PAST)

    def testUsercouponsByTemplate(self):
        get_data = {"template_id": 1}
        response = self.client.get(self.url_usercoupons_by_template, get_data, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        results = data['results']
        for user_coupon in results:
            self.assertEqual(user_coupon['template_id'], 1)

    def testCreateUsercoupon(self):
        post_data = {"template_id": 1}
        response = self.client.post(self.url_user_coupons, post_data, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        assert (data['code'] in [0, 6, 7, 9])

    def testChooseCouponByProduct(self, pk=15):
        post_item = {"pro_num": 1, "item_id": 41385}
        url = self.url_choose_coupon.format(pk)
        response = self.client.post(url, post_item, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

    def testChooseCouponByShoppingCart(self, pk=15):
        post_cart = {"cart_ids": '422898,422897'}
        url = self.url_choose_coupon.format(pk)
        response = self.client.post(url, post_cart, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

    def testChooseCouponByCategory(self, pk=15):
        post_cart = {"cart_ids": '422898,422897'}
        url = self.url_choose_coupon.format(pk)
        response = self.client.post(url, post_cart, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        assert (data['res'] == 1)


class CouponTemplate(TestCase):
    fixtures = [
        "test.flashsale.coupon.coupontemplate.json",
        "test.flashsale.coupon.customer.json",
        "test.flashsale.coupon.usercoupon.json"
    ]
    url_useful_coupontemplates = '/rest/v2/cpntmpl'

    def setUp(self):
        self.username = '13739234188'
        self.password = '123456'
        self.client.login(username=self.username, password=self.password)

    def testUsefulTemplates(self):
        response = self.client.get(self.url_useful_coupontemplates, {}, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        for template in data:
            assert (template['status'] in [1, 2])


class OrderShareCouponTestCase(TestCase):
    fixtures = [
        "test.flashsale.coupon.customer.json",
        "test.flashsale.coupon.saletrade.json",
        "test.flashsale.coupon.coupontemplate.json",
        "test.flashsale.coupon.ordersharecoupon.json",
        # "test.flashsale.coupon.xlampleorder.json",
    ]
    url_user_coupons = '/rest/v2/usercoupons'  # 用户优惠券
    url_create_order_share = '/rest/v2/sharecoupon/create_order_share'
    url_create_active_share = '/rest/v2/sharecoupon/create_active_share'
    url_pick_order_share_coupon = '/rest/v2/sharecoupon/pick_order_share_coupon'
    url_pick_active_share_coupon = '/rest/v2/sharecoupon/pick_active_share_coupon'

    def setUp(self):
        self.username = 'o29cQs-ONn2PxIYYducFkQcmkpGc'
        self.password = '123456'
        self.client.login(username=self.username, password=self.password)

    def testCreateOrderShareCouponCode1(self):
        data = {}
        response = self.client.post(self.url_create_order_share, data, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 1)

    def testCreateOrderShareCouponCheckTrade(self):
        data = {"uniq_id": "xd160426571f12d01282b"}  # 验证订单
        response = self.client.post(self.url_create_order_share, data, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 4)

    def testCreateOrderShareCoupon(self):
        data = {"uniq_id": "xd16040657050c243dc16", "ufrom": "wx"}  # 正确的tid
        response = self.client.post(self.url_create_order_share, data, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        order_share = OrderShareCoupon.objects.all().order_by('-created').first()
        self.assertEqual(order_share.platform_info, {u'wx': 1})
        self.assertEqual(data['code'], 0)

    def testCreateActiveShare(self):
        """ 测试活动分享  """
        data = {"uniq_id": "3_9", "ufrom": "wx"}  # 正确的 活动 和 用户
        response = self.client.post(self.url_create_active_share, data, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        order_share = OrderShareCoupon.objects.all().order_by('-created').first()
        self.assertEqual(order_share.platform_info, {u'wx': 1})
        self.assertEqual(data['code'], 0)

    def testPickOrderShareCoupon(self):
        return
        data = {"uniq_id": "xd16040657050c243dc15", "ufrom": "wx"}  # 正确的tid
        response = self.client.post(self.url_pick_order_share_coupon, data, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 0)
        # 获取当前用户优惠券 并查看类型
        response = self.client.get(self.url_user_coupons, {}, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        coupon = data['results'][0]
        self.assertEqual(coupon['status'], UserCoupon.UNUSED)
        self.assertEqual(coupon['coupon_type'], UserCoupon.TYPE_ORDER_SHARE)


class TmpShareCouponTestCase(TestCase):
    fixtures = [
        "test.flashsale.coupon.tmpsharecoupon.json",
        "test.flashsale.coupon.ordersharecoupon.json",
    ]

    url_create_temp = "/rest/v2/tmpsharecoupon"

    def setUp(self):
        pass

    def testCreateTempShareCoupon1(self):
        data = {}
        response = self.client.post(self.url_create_temp, data, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 1)

    def testCreateTempShareCoupon2(self):
        data = {"mobile": "13739234188", "uniq_id": "dadfqw"}
        response = self.client.post(self.url_create_temp, data, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 2)

    def testCreateTmpCoupon(self):
        data = {"mobile": "13739234188", "uniq_id": "xd16040657050c243dc15"}
        response = self.client.post(self.url_create_temp, data, ACCPET='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 3)
