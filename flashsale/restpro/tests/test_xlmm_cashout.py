# coding=utf-8
__author__ = 'jishu_linjie'
import json
from django.test import TestCase
from flashsale.xiaolumm.models import CashOut, MamaFortune
from flashsale.pay.models import BudgetLog


class MamaCahoutTestCase(TestCase):
    fixtures = [
        'test.flashsale.xiaolumm.cashout.customer.json',
        'test.flashsale.xiaolumm.cashout.xiaolumm.json',
        'test.flashsale.xiaolumm.cashout.cashout.json',
        'test.flashsale.pay.userbudget.json',
        # 'test.flashsale.xiaolumm.cashout.mamafortune.json', #创建xiaolumama时会触发signal添加mamaforturn
        'test.flashsale.xiaolumm.cashout.usergroup.json',
    ]

    url_cashout_list = '/rest/v1/pmt/cashout'
    url_cashout_to_budget = '/rest/v1/pmt/cashout/cashout_to_budget'

    def setUp(self):
        self.username = 'o29cQs-ONn2PxIYYducFkQcmkpGc'
        self.password = '123456'
        self.client.login(username=self.username, password=self.password)
        mama_ft = MamaFortune.objects.filter(mama_id=1461).first()
        if mama_ft:
            mama_ft.active_value_num = 100
            mama_ft.carry_confirmed = 28000
            mama_ft.carry_pending = 1000
            mama_ft.order_num = 2
            mama_ft.fans_num = 1
            mama_ft.history_last_day = '2016-03-23'
            mama_ft.save()
        else:
            mama_ft = MamaFortune()
            mama_ft.mama_id = 1461
            mama_ft.active_value_num = 100
            mama_ft.carry_confirmed = 28000
            mama_ft.carry_pending = 1000
            mama_ft.order_num = 2
            mama_ft.fans_num = 1
            mama_ft.history_last_day = '2016-03-23'
            mama_ft.save()

    def testCashoutList(self):
        response = self.client.get(self.url_cashout_list, {}, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        complte_count = 0  # 审核的只有1条(默认0条)
        cashout = data['results'][0]
        self.assertEqual(cashout['xlmm'], 1461)
        self.assertEqual(cashout['status'], CashOut.COMPLETED)

    def testCashoutChoiceCreate(self):
        """ 兼容测试 选择提现金额测试 """
        post_data = {"choice": "c1"}
        response = self.client.post(self.url_cashout_list, post_data, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        assert data['code'] == 0

    def testCashoutInputCreate(self):
        """ 填写金额提现 """
        post_data = {"cashout_amount": "1.5"}
        response = self.client.post(self.url_cashout_list, post_data, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        assert data['code'] == 0
        cashouts = CashOut.objects.filter(xlmm=1461, status=CashOut.PENDING)
        assert cashouts.count() == 1
        assert cashouts.first().value == 150

    def testCshoutToBudget(self):
        """ 代理提现到钱包"""
        post_data = {"cashout_amount": "1.5"}
        response = self.client.post(self.url_cashout_to_budget, post_data, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        assert data['code'] == 0
        cashouts = CashOut.objects.filter(xlmm=1461, status=CashOut.APPROVED)
        assert cashouts.count() == 1
        assert cashouts.first().value == 150
        budget = BudgetLog.objects.order_by('-created').first()
        assert budget.flow_amount == 150
        assert budget.budget_type == BudgetLog.BUDGET_IN
        assert budget.budget_log_type == BudgetLog.BG_MAMA_CASH
        # 断言 是代理提现类型