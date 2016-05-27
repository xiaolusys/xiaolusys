# coding:utf-8
from django.test import TestCase
import json

import logging
logger = logging.getLogger(__name__)

class SaletradeTestCase(TestCase):
    """ 登陆 / 加入购物车 / 获取支付信息 /付款 /查看付款订单 """
    fixtures = ['test.flashsale.customer.json',
                'test.flashsale.pay.logistics.companys.json',
                'test.shopback.categorys.productcategory.json',
                'test.shopback.items.product.json',
                'test.flashsale.pay.shoppingcart.json',
                'test.flashsale.pay.useraddress.json',
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

    def getCartPayinfo(self,cart_ids=''):
        response = self.client.get('/rest/v1/carts/carts_payinfo',
                                   {'cart_ids': cart_ids},
                                   ACCEPT='application/json; q=0.01')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        return data

    def addShoppingCart_V2(self):
        pdata = {'num': 3, 'item_id': 40874, 'sku_id': 164886}
        response = self.client.post('/rest/v2/carts',
                                    pdata,
                                    ACCEPT='application/json; q=0.01')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 0)

    def getShoppingCarts_V2(self):
        response = self.client.get('/rest/v2/carts',
                                   ACCEPT='application/json; q=0.01')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['num'], 3)
        return data

    def getCartPayinfo_V2(self, cart_ids=''):
        response = self.client.get('/rest/v2/carts/carts_payinfo',
                                   {'cart_ids': cart_ids, 'device': 'wap'},
                                   ACCEPT='application/json; q=0.01')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        return data

    def testCartPayInfo_V1(self):

        self.addShoppingCart()
        cart_list = self.getShoppingCarts()

        cart_idstr = ','.join([str(c['id']) for c in cart_list])
        cart_num   = len(cart_list)

        data = self.getCartPayinfo(cart_ids=cart_idstr)

        self.assertGreater(data['total_fee'],0)
        self.assertGreater(data['total_payment'], 0)
        self.assertEqual(len(data['cart_list']), cart_num)
        return data

    def testCartPayInfo_V2(self):
        self.addShoppingCart_V2()
        cart_list = self.getShoppingCarts_V2()

        cart_idstr = ','.join([str(c['id']) for c in cart_list])
        cart_num = len(cart_list)

        data = self.getCartPayinfo_V2(cart_ids=cart_idstr)

        self.assertGreater(data['total_fee'], 0)
        self.assertGreater(data['total_payment'], 0)
        self.assertEqual(len(data['cart_list']), cart_num)
        self.assertGreater(len(data['logistics_companys']), 0)
        return data

    def getUserAddress(self):
        response = self.client.get('/rest/v1/address',
                                   ACCEPT='application/json; q=0.01')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertGreater(len(data),0)
        return data[0]


    def testShoppingcartAlipayCharge_V1(self):

        cart_ids = '422913,422912'
        addr     = self.getUserAddress()
        scp_info = self.getCartPayinfo(cart_ids=cart_ids)
        channel = 'alipay'
        self.assertTrue(scp_info['alipay_payable'])
        post_data = {
            'uuid': scp_info['uuid'],
            'cart_ids': cart_ids,
            'payment':scp_info['total_payment'],
            'post_fee':scp_info['post_fee'],
            'discount_fee':scp_info['discount_fee'],
            'total_fee':scp_info['total_fee'],
            'buyer_message':'',
            'addr_id':addr['id'],
            'channel':channel,
            'logistic_company_id': '-2',
            'csrfmiddlewaretoken':'OoVZZqTFa4d0c1oNhwPyI1ikmYrdGyZF',
            'mm_linkid':'1',
            'ufrom':'web',
        }
        logger.debug('charge before:%s'% post_data)

        response = self.client.post('/rest/v1/trades/shoppingcart_create',
                                    post_data,
                                   ACCEPT='application/json; q=0.01')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['channel'],channel)
        self.assertEqual(data['amount'], int(post_data['payment'] * 100))


    def testShoppingcartAlipayCharge_V2(self):
        cart_ids = '422913,422912'
        addr = self.getUserAddress()
        scp_info = self.getCartPayinfo_V2(cart_ids=cart_ids)
        channel_key = 'alipay_wap'
        channel = None
        for cn in scp_info['channels']:
            if cn['id'] == channel_key:
                channel = cn
        self.assertIsNotNone(channel)
        self.assertTrue(channel['payable'])

        post_data = {
            'uuid': scp_info['uuid'],
            'cart_ids': cart_ids,
            'payment': scp_info['total_payment'],
            'post_fee': scp_info['post_fee'],
            'discount_fee': scp_info['discount_fee'],
            'total_fee': scp_info['total_fee'],
            'buyer_message': '',
            'addr_id': addr['id'],
            'channel': channel_key,
            'logistic_company_id': '100',
            'csrfmiddlewaretoken': 'OoVZZqTFa4d0c1oNhwPyI1ikmYrdGyZF',
            'mm_linkid': '1',
            'ufrom': 'web',
        }
        logger.debug('charge before:%s' % post_data)
        response = self.client.post('/rest/v2/trades/shoppingcart_create',
                                    post_data,
                                    ACCEPT='application/json; q=0.01')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 0)
        self.assertEqual(data['charge']['channel'], channel_key)
        self.assertEqual(data['charge']['amount'], int(post_data['payment'] * 100))

    # def testShoppingcartBudgetCharge(self):
    #     pass




