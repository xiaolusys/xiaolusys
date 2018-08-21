# encoding=utf8
"""
计算精品汇indirect返点

执行本程序前,请注意填写月份
"""
from decimal import Decimal
from datetime import datetime
from django.db.models import F, Sum, Q
from django.core.management.base import BaseCommand

from flashsale.pay.models import BudgetLog
from flashsale.pay.models.trade import SaleOrder
from flashsale.xiaolumm.models.models import XiaoluMama
from flashsale.coupon.models.transfer_coupon import CouponTransferRecord
from flashsale.xiaolumm.apis.v1.xiaolumama import task_calc_xlmm_elite_score, get_mama_buy_coupon_score


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments '2017-06'
        parser.add_argument('ymdate', nargs='+', type=str)

    def handle(self, *args, **options):
        """
        计算精品汇返点, 并发放
        """
        ym_date = options.get('ymdate')[0]
        year_months = ym_date.split('-')
        if not len(year_months) == 2:
            print 'invalid ymdate, need eg: 2017-06'
            return

        year, month = map(int , year_months)
        end_month = month % 12 + 1
        end_year  = month / 12 + year
        start_date = datetime(year, month, 1)  # 这里要改
        end_date = datetime(end_year, end_month, 1)  # 这里也要改

        mamas = self.get_mamas_score_gte()

        for mama in mamas:
            res = self.cal_mama_score(mama.id, start_date, end_date)
            fd = res['fd']
            if res['fd'] > 0:
                print '---'
                print res['start_date'], res['end_date']
                print mama.id
                print u'返点:{fd}, 买券额: {payment}, 积分: {score} \n'.format(**res)


    def get_mamas_score_gte(self, score=6000):
        mamas = XiaoluMama.objects.filter(elite_score__gte=score, referal_from=XiaoluMama.INDIRECT)
        return mamas


    def cal_mama_score(self, mama_id, start_date, end_date):
        score, upgrade_date = task_calc_xlmm_elite_score(mama_id)
        if start_date < upgrade_date:
            start_date = upgrade_date
        return get_mama_buy_coupon_score(mama_id, start_date, end_date)
