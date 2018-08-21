import datetime
from django.test import TestCase, tag
import json

import base64
import Image
from cStringIO import StringIO
from core.ocr import idcard

class OcrTestCase(TestCase):

    fixtures = ['test.flashsale.customer.json']

    def setUp(self):
        self.client.login(username='xiaolu', password='test')

    @tag('C')
    def testCardIndentify(self):
        # io = open('/home/meron/Desktop/mxq/IMG_2532.jpg', 'rb').read()
        base64_string = base64.b64encode('ABC')
        response = self.client.post(
            '/rest/v2/ocr/idcard_indentify',
            {'side': 'face', 'card_base64': base64_string},
            ACCEPT='application/json; q=0.01'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        # self.assertEqual(data['code'], 0)