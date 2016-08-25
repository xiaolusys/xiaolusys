# coding:utf-8
import json
import datetime
from django.db.models import Count
from django.test import TestCase

from flashsale.xiaolumm.models import XiaoluMama, MamaMission, MamaMissionRecord
from flashsale.xiaolumm.tasks import task_update_all_mama_mission_state

import logging
logger = logging.getLogger(__name__)

class SaletradeTestCase(TestCase):
    """ 登陆 / 加入购物车 / 获取支付信息 /付款 /查看付款订单 """
    fixtures = [
        'test.flashsale.customer.json',
        'test.flashsale.xiaolumm.json',
        'test.flashsale.xiaolumm.weeklyaward.json'
    ]

    def setUp(self):
        self.mama_id = 44
        self.year_week = datetime.datetime.now().strftime('%Y-%W')
        MamaMissionRecord.objects.update(year_week=self.year_week )

    def testUpdateAllMamaMissionState(self):
        MamaMissionRecord.objects.all().delete()
        task_update_all_mama_mission_state()

        missions = MamaMissionRecord.objects.filter(
            mama_id=self.mama_id,
            year_week=self.year_week,
            status=MamaMissionRecord.STAGING
        )
        missions_agg = dict(missions.annotate(record_count=Count('id')).values_list('mission__cat_type','record_count'))

        self.assertEqual(missions_agg[MamaMission.CAT_TRIAL_MAMA], 1)
        self.assertEqual(missions_agg[MamaMission.CAT_REFER_MAMA], 1)


    # def getShoppingCarts(self):
    #     response = self.client.get('/rest/v1/carts',
    #                                ACCEPT='application/json; q=0.01')
    #     self.assertEqual(response.status_code, 200)
    #     data = json.loads(response.content)
    #     self.assertGreater(len(data), 0)
    #     return data





