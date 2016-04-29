# coding:utf-8
from django.test import TestCase
import json

class SaletradeTestCase(TestCase):
    """ 登陆 / 加入购物车 / 获取支付信息 /付款 /查看付款订单 """
    fixtures = ['test.flashsale.customer.json',
                'test.shopback.categorys.productcategory.json',
                'test.shopback.items.product.json',
                ]
    def setUp(self):
        self.username = 'xiaolu'
        self.password = 'test'
        self.client.login(username=self.username, password=self.password)

    def addShoppingCart(self):
        pdata = {'num': 1, 'item_id': 40874, 'sku_id': 164886}
        response = self.client.post('/rest/v1/carts',
                                    pdata,
                                    ACCEPT='application/json; q=0.01')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 0)

    def getShoppingCarts(self):
        response = self.client.get('/rest/v1/carts',
                                   ACCEPT='application/json; q=0.01')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertGreater(len(data), 0)
        return data

    def testGetCartPayInfo(self):

        self.addShoppingCart()
        cart_list = self.getShoppingCarts()

        cart_idstr = ','.join([str(c['id']) for c in cart_list])
        cart_num   = len(cart_list)

        response = self.client.get('/rest/v1/carts/carts_payinfo',
                                   {'cart_ids':cart_idstr},
                                   ACCEPT = 'application/json; q=0.01')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertGreater(data['total_fee'],0)
        self.assertGreater(data['total_payment'], 0)
        self.assertEqual(len(data['cart_list']), cart_num)



