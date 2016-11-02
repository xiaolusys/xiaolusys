# coding=utf-8
__author__ = 'jishu_linjie'

import json
from django.test import TestCase


class UserAddressTestCase(TestCase):
    fixtures = [
        'test.flashsale.pay.useraddress.customer.json',
        'test.shopback.categorys.productcategory.json',
        'test.shopback.items.product.json',
        'test.flashsale.pay.logistics.companys.json',
        'test.flashsale.pay.useraddress.address.json',
        'test.flashsale.pay.saletrade.json',
    ]

    def setUp(self):
        self.username = '13739234188'
        self.password = '123456'
        self.client.login(username=self.username, password=self.password)

    def testUserAddress(self):
        response = self.client.get('/rest/v1/address', {}, ACCEPT='application/json;')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)
        for address in data:
            self.assertEqual(address['status'], 'normal')

    def getOneAddress(self, address_id):
        response = self.client.get('/rest/v1/address/get_one_address', {'id':address_id}, ACCEPT='application/json;')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        return data[0]

    def testCreateUserAddress(self):
        address = {
            "default": 'true',
            "receiver_state": "安徽省",
            "receiver_city": "安庆市",
            "receiver_district": "桐城县",
            "receiver_address": "中义乡",
            "receiver_name": "林杰",
            "receiver_mobile": "13739234188",
            # "logistic_company_code":"YUNDA_QR"
        }

        response = self.client.post('/rest/v1/address/create_address', address, ACCEPT='application/json;')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)  # 创建的返回结果
        self.assertEqual(data['ret'], True)  # 添加成功
        self.assertGreater(data['result']['address_id'],0)
        address_id = data['result']['address_id']
        # 添加过后查询地址
        response = self.client.get('/rest/v1/address', {}, ACCEPT='application/json;')
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 3)

        resp_address = self.getOneAddress(address_id)
        for k ,v in address.items():
            if k == 'default':
                v = v and True or False
            self.assertEqual(resp_address.get(k),v)

    def testUpdateUserAddress(self):
        address = {
            "default": 'true',
            "receiver_state": "安徽省",
            "receiver_city": "安庆市",
            "receiver_district": "桐城县",
            "receiver_address": "中义乡",
            "receiver_name": "林杰",
            "receiver_mobile": "13739234188",
            # "logistic_company_code": "YUNDA_QR",
            "referal_trade_id": ''
        }

        response = self.client.post('/rest/v1/address/111452/update', address, ACCEPT='application/json;')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)  # 创建的返回结果
        self.assertEqual(data['ret'], True)  # 添加成功
        self.assertGreater(data['result']['address_id'], 0)
        address_id = data['result']['address_id']

        address.pop('referal_trade_id')
        resp_address = self.getOneAddress(address_id)
        for k, v in address.items():
            if k == 'default':
                v = v and True or False
            self.assertEqual(resp_address.get(k), v)

    def testUpdateAddressCompanyCode(self):
        address = {
            "logistic_company_code": "YUNDA_QR",
            "referal_trade_id": 333231
        }

        response = self.client.post('/rest/v1/address/111452/change_company_code', address, ACCEPT='application/json;')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)  # 创建的返回结果
        self.assertEqual(data['code'], 0)  # 添加成功





