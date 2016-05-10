from django.test import TestCase
import json

class SaleRefundTestCase(TestCase):

    fixtures = ['test.flashsale.customer.json',
                'test.flashsale.pay.saletrade.json'
                ]

    def setUp(self):
        self.username = 'xiaolu'
        self.password = 'test'
        self.client.login(username=self.username, password=self.password)

    def createRefundNoReturnGoods(self):

        pass


    def createRefundReturnGoods(self):
        pass
