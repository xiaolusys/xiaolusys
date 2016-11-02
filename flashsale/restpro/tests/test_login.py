from django.test import TestCase
import json
from flashsale.pay.models import Customer
class AuthenticationTestCase(TestCase):

    fixtures = ['test.flashsale.customer.json']

    def setUp(self):
        self.username = '18621623915'
        self.password = 'test'

    def testLogin(self):
        response = self.client.post('/rest/v2/passwordlogin',
                                    {'username':self.username,'password':self.password},
                                    ACCPET='application/json;')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['rcode'], 0)
        self.assertIn('sessionid', self.client.cookies)


