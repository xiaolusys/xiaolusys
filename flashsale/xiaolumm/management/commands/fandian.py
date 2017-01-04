# encoding=utf8
"""
计算精品汇返点, 并发放到个人钱包

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


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        计算精品汇返点, 并发放
        """

        month = 12  # 哪个月的返点, 需要你自己填
        start_date = datetime(2016, 12, 1)  # 这里要改
        end_date = datetime(2017, 1, 1)  # 这里也要改

        mamas = self.get_mamas_score_gte()

        for mama in mamas:
            res = self.cal_mama_score(mama.id, start_date, end_date)
            fd = res['fd']
            if res['fd'] > 0:
                print '---'
                print res['start_date'], res['end_date']
                print mama.id
                print u'返点:{fd}, 买券额: {payment}, 积分: {score} \n'.format(**res)

                customer_id = mama.customer_id
                flow_amount = int(Decimal(str(fd)) * 100)
                uni_key = 'fd-{month}-{mama_id}'.format(month=12, mama_id=mama.id)
                try:
                    # 创建待确定收入
                    BudgetLog.create(customer_id, BudgetLog.BUDGET_IN, flow_amount, BudgetLog.BG_FANDIAN,
                         status=BudgetLog.PENDING, uni_key=uni_key)
                except Exception:
                    print u'{mama_id}在{month}月的返点已经发过了'.format(mama_id=mama.id, month=month)
                    continue


    def task_calc_xlmm_elite_score(self, mama_id):
        if mama_id <= 0:
            return

        records = CouponTransferRecord.objects.filter(
            Q(coupon_from_mama_id=mama_id) | Q(coupon_to_mama_id=mama_id),
            transfer_status=CouponTransferRecord.DELIVERED).order_by('created')

        score = 0
        upgrade_date = None
        for record in records:

            if record.coupon_from_mama_id == mama_id:
                if record.transfer_type in [CouponTransferRecord.OUT_CASHOUT, CouponTransferRecord.IN_RETURN_COUPON]:
                    score = score - record.elite_score

            if record.coupon_to_mama_id == mama_id:
                if record.transfer_type in [
                    CouponTransferRecord.IN_BUY_COUPON,
                    CouponTransferRecord.OUT_TRANSFER,
                    CouponTransferRecord.IN_GIFT_COUPON
                ]:
                    score += record.elite_score
                    # print record.created, record.elite_score, score

            if score >= 3000 and upgrade_date is None:
                upgrade_date = record.created

        return score, upgrade_date


    def get_mama_buy_coupon_score(self, mama_id, start_date, end_date):
        score = 0
        payment = 0
        records = CouponTransferRecord.objects.filter(
            coupon_to_mama_id=mama_id,
            transfer_status=CouponTransferRecord.DELIVERED,
            transfer_type=CouponTransferRecord.IN_BUY_COUPON,
            created__gt=start_date,
            created__lt=end_date,
        )
        for record in records:
            order_id = record.order_no
            try:
                order = SaleOrder.objects.get(oid=order_id)
            except Exception:
                continue
            payment += order.payment
            score += record.elite_score

        fd = 0
        if 10000 <= payment < 20000:
            fd = payment * 0.01
        elif 20000 <= payment < 50000:
            fd = payment * 0.02
        elif 50000 <= payment < 100000:
            fd = payment * 0.03
        elif 100000 <= payment < 150000:
            fd = payment * 0.05
        elif 150000 <= payment < 200000:
            fd = payment * 0.06
        elif 200000 <= payment < 300000:
            fd = payment * 0.07
        elif 300000 <= payment < 400000:
            fd = payment * 0.08
        elif 400000 <= payment < 500000:
            fd = payment * 0.09
        elif payment >= 500000:
            fd = payment * 0.10

        return {'score': score, 'payment': payment, 'fd': fd, 'start_date': start_date, 'end_date': end_date}


    def get_mamas_score_gte(self, score=3000):
        mamas = XiaoluMama.objects.filter(elite_score__gte=score, referal_from=XiaoluMama.DIRECT)
        return mamas


    def cal_mama_score(self, mama_id, start_date, end_date):
        score, upgrade_date = self.task_calc_xlmm_elite_score(mama_id)
        if start_date < upgrade_date:
            start_date = upgrade_date
        return self.get_mama_buy_coupon_score(mama_id, start_date, end_date)
