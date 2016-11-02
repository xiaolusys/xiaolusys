# -*- coding:utf-8 -*-

from django.test import TestCase
from flashsale.pay.models import SaleTrade
from flashsale.restpro import kdn_wuliu_extra
class KdnTestCase(TestCase):
    def setUp(self):
        st_data = {'id':1,'tid':'abc',"buyer_id":88}
        st_data2 = {'id':2, 'tid':'def',"buyer_id":88}

        SaleTrade.objects.create(**st_data)
        SaleTrade.objects.create(**st_data2)

        self.saletrade = SaleTrade.objects.get(id=2)

        # self.saletrade = SaleTrade.objects.get(id=1)

    def test_get_trade(self):
        self.assertEqual(self.saletrade,kdn_wuliu_extra.get_trade(self.saletrade.tid))
        self.assertEqual(self.saletrade,kdn_wuliu_extra.get_trade(self.saletrade.id))

