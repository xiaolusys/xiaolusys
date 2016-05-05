# coding=utf-8
__author__ = 'jishu_linjie'
import json
from django.test import TestCase
from flashsale.xiaolumm.models import CashOut
from flashsale.pay.models_user import BudgetLog


class MamaCahoutTestCase(TestCase):
    fixtures = [
        'test.flashsale.xiaolumm.cashout.customer.json',
        'test.flashsale.xiaolumm.cashout.cashout.json',
        'test.flashsale.xiaolumm.cashout.mamafortune.json',
        'test.flashsale.xiaolumm.cashout.xiaolumm.json',
        'test.flashsale.xiaolumm.cashout.usergroup.json',
    ]

    url_cashout_list = '/rest/v1/pmt/cashout'
    url_cashout_to_budget = '/rest/v1/pmt/cashout/cashout_to_budget'

    def setUp(self):
        self.username = 'o29cQs-ONn2PxIYYducFkQcmkpGc'
        self.password = '123456'
        self.client.login(username=self.username, password=self.password)

    def testCashoutList(self):
        response = self.client.get(self.url_cashout_list, {}, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        complte_count = 0  # 审核的只有1条(默认0条)
        for cashout in data:
            self.assertEqual(cashout['xlmm'], 1461)
            if cashout['status'] == CashOut.COMPLETED:
                complte_count += 1
        self.assertEqual(complte_count, 1)

    def testCashoutChoiceCreate(self):
        """ 兼容测试 选择提现金额测试 """
        post_data = {"choice": "c1"}
        response = self.client.post(self.url_cashout_list, post_data, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        assert data['code'] in [0, 1, 2, 3, 4]

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


