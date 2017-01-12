from django.test import TestCase
import json

class SaleRefundTestCase(TestCase):

    fixtures = ['test.flashsale.pay.useraddress.customer.json',
                'test.shopback.categorys.productcategory.json',
                'test.shopback.items.product.json',
                'test.flashsale.pay.logistics.companys.json',
                'test.flashsale.pay.useraddress.address.json',
                'test.flashsale.pay.saletrade.json',
                ]

    def setUp(self):
        from flashsale.pay.models import SaleOrder
        SaleOrder.objects.get(id=368347).set_psi_paid()
        self.username = 'xiaolu'
        self.password = 'test'
        self.client.login(username=self.username, password=self.password)

    def getSaleorderInfo(self, trade_id , order_id):
        response = self.client.get('/rest/v1/trades/%s/orders/%s'%(trade_id, order_id),
                                   ACCEPT='application/json; q=0.01')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsNot(data['refund_id'], '')
        return data

    def getRefundInfo(self, trade_id, order_id):
        order_json = self.getSaleorderInfo(trade_id, order_id)
        response = self.client.get('/rest/v1/refunds/%s' % (order_json['refund_id']),
                                   ACCEPT='application/json; q=0.01')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        return data

    def testCreateRefund(self):
        trade_id, order_id = 332233, 368347
        pdata = {
            'id': order_id,
            'reason': 10,
            'num': 1,
            'description':'abc',
            'proof_pic':'http://test.jpg',
        }
        response = self.client.post('/rest/v1/refunds', pdata,
                                    ACCEPT='application/json; q=0.01')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 0)
        refund = self.getRefundInfo(trade_id, order_id)
        self.assertEqual(refund['refund_num'], pdata['num'])
        self.assertNotEqual(refund['reason'],'')
        self.assertEqual(refund['desc'], pdata['description'])
        self.assertEqual(refund['proof_pic'][0], pdata['proof_pic'])
        self.assertEqual(refund['status'], 7)

    def testCreateFastRefund(self):
        trade_id, order_id = 332233, 368347
        pdata = {
            'id': order_id,
            'reason': 10,
            'num': 1,
            'description': 'abc',
            'proof_pic': 'http://test.jpg',
            'refund_channel': 'budget',
        }
        response = self.client.post('/rest/v1/refunds', pdata,
                                    ACCEPT='application/json; q=0.01')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 0)
        refund = self.getRefundInfo(trade_id, order_id)
        self.assertEqual(refund['refund_num'], pdata['num'])
        self.assertNotEqual(refund['reason'], '')
        self.assertEqual(refund['desc'], pdata['description'])
        self.assertEqual(refund['proof_pic'][0], pdata['proof_pic'])
        self.assertEqual(refund['refund_channel'], pdata['refund_channel'])
        self.assertEqual(refund['status'], 7)

    def createRefundNoReturnGoods(self):

        pass


    def createRefundReturnGoods(self):
        pass
