# encoding=utf8
from django.test import TestCase
import json


class FavoritesTestCase(TestCase):

    fixtures = ['test.flashsale.customer.json']

    def setUp(self):
        self.username = 'xiaolu'
        self.password = 'test'

    def testCreateFavorites(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.post(
            '/rest/v1/favorites',
            {'model_id': 1},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn(data['code'], [0, 1])

    def testListFavorites(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get('/rest/v1/favorites')
        self.assertEqual(response.status_code, 200)

    def testDeleteFavorites(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.delete(
            '/rest/v1/favorites',
            data=json.dumps({'model_id': 1}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['code'], 0)
