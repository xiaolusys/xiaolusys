import datetime
from django.test import TestCase
import json

class PortalTestCase(TestCase):

    fixtures = ['test.flashsale.activity.json',
                'test.flashsale.brands.json',
                'test.flashsale.posters.json',
                'test.shopback.categorys.productcategory.json',
                'test.shopback.items.product.json',
                ]

    def setUp(self):
        from flashsale.pay.models import GoodShelf
        goodshelf = GoodShelf.objects.all().first()
        goodshelf.active_time = datetime.datetime.now()
        goodshelf.save()

    def testListUrl(self):
        response = self.client.get('/rest/v1/portal', ACCEPT='application/json; q=0.01')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertGreater(len(data['categorys']), 0)
        self.assertEqual(len(data['posters']), 2)



    

