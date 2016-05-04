# coding=utf-8
__author__ = 'jishu_linjie'

import json
from django.test import TestCase


class UserAddressTestCase(TestCase):
    fixtures = [
        'test.flashsale.pay.useraddress.customer.json',
        'test.flashsale.pay.useraddress.address.json',
    ]

    url_user_address = '/rest/v1/address'
    url_add_user_address = '/rest/v1/address/create_address'

    def setUp(self):
        self.username = '13739234188'
        self.password = '123456'
        self.client.login(username=self.username, password=self.password)

    def testUserAddress(self):
        response = self.client.get(self.url_user_address, {}, ACCEPT='application/json;')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)
        for address in data:
            self.assertEqual(address['status'], 'normal')

    def testCreateUserAddress(self):
        address = {
            "default": '1',
            "receiver_state": "安徽省",
            "receiver_city": "安庆市",
            "receiver_district": "桐城县",
            "receiver_address": "中义乡",
            "receiver_name": "林杰",
            "receiver_mobile": "13739234188"
        }

        response = self.client.post(self.url_add_user_address, address, ACCEPT='application/json;')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)  # 创建的返回结果
        self.assertEqual(data['ret'], True)  # 添加成功
        # 添加过后查询地址
        response = self.client.get(self.url_user_address, {}, ACCEPT='application/json;')
        data = json.loads(response.content)
        self.assertEqual(len(data), 3)
        for address in data:
            if address['receiver_district'] == "桐城县":
                self.assertEqual(address['default'], True)  # 新创建的设置了默认地址后
            else:
                self.assertEqual(address['default'], False)


