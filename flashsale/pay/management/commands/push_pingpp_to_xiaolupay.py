# coding=utf-8
__author__ = 'jishu_linjie'
from django.core.management.base import BaseCommand, CommandError
from datetime import timedelta

from django.db.models import Q
from flashsale.pay.models import SaleTrade, SaleRefund
from mall.xiaolupay.models import ChargeOrder, RefundOrder

class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('start_date', nargs='+', type=str)

    def create_charge_order(self, st):
        return ChargeOrder.objects.create(
            order_no=st.tid,
            channel=st.channel,
            paid=st.pay_time is not None,
            amount=int((st.pay_cash or st.payment) * 100),
            time_paid=st.pay_time,
            time_expire=st.pay_time and st.pay_time + timedelta(seconds=7200),
        )

    def handle(self, *args, **options):
        start_date = options.get('start_date')[0]

        sts = SaleTrade.objects.filter(charge__startswith='ch_',
                                       created__gte=start_date,
                                       channel__in=['wx','wx_pub','alipay','alipay_wap'])
        print 'update saletrade count= ', sts.count()
        for st in sts.iterator():
            ch = ChargeOrder.objects.filter(order_no=st.tid).first()
            if ch:
                continue
            self.create_charge_order(st)

        sfs = SaleRefund.objects.filter(created__gte=start_date,
                                        refund_id__startswith='re_')
        print 'update salerefund count= ', sfs.count()
        for sf in sfs.iterator():
            rch = RefundOrder.objects.filter(Q(refund_no=sf.sale_trade.tid)|Q(refund_no=sf.refund_no)).first()
            if rch:
                continue

            charge_order = ChargeOrder.objects.filter(order_no=sf.sale_trade.tid).first()
            if not charge_order:
                charge_order = self.create_charge_order(sf.sale_trade)

            RefundOrder.objects.create(
                refund_no=sf.sale_trade.tid,
                amount=int(sf.refund_fee * 100),
                succeed=sf.success_time is not None,
                status=sf.REFUND_SUCCESS and RefundOrder.SUCCESSED or RefundOrder.PENDING,
                time_succeed=sf.success_time,
                charge=charge_order,
                charge_order_no=sf.sale_trade.tid,
            )



