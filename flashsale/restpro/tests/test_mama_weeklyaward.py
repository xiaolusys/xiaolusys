# coding=utf-8
__author__ = 'jishu_linjie'
import json
import datetime
from django.test import TestCase
from flashsale.xiaolumm.tasks import task_update_all_mama_mission_state

class MamaMissionTestCase(TestCase):
    fixtures = [
        'test.flashsale.customer.json',
        'test.flashsale.xiaolumm.json',
        'test.flashsale.xiaolumm.weeklyaward.json'
    ]


    def setUp(self):
        self.username = 'xiaolu'
        self.password = 'test'
        self.client.login(username=self.username, password=self.password)

    def testMamaMissonWeeklylist(self):
        task_update_all_mama_mission_state()

        _url = '/rest/v2/mama/mission/weeklist.json'
        response = self.client.get(_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertGreater(len(data['personal_missions']), 1)
        self.assertEqual(len(data['group_missions']), 0)