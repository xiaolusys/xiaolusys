# coding=utf-8
__author__ = 'jishu_linjie'
import json
import datetime
from django.test import TestCase
from flashsale.xiaolumm.models import XiaoluMama, MamaMission, MamaMissionRecord

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

        year_week = datetime.datetime.now().strftime('%Y-%W')
        MamaMissionRecord.objects.update(year_week=year_week)

    def testMamaMissonWeeklylist(self):
        _url = '/rest/v2/mama/mission/weeklist.json'
        response = self.client.get(_url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data['personal_missions']), 6)
        self.assertEqual(len(data['group_missions']), 2)