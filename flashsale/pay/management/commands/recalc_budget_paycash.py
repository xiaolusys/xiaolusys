# encoding=utf8
# author: meron@2017.4.26
from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from flashsale.pay.models.trade import SaleTrade
from statistics.daystats.tasks import task_Push_Sales_To_DailyStat

class Command(BaseCommand):
    def handle(self, *args, **options):

        sts = SaleTrade.objects.filter(
            channel=SaleTrade.BUDGET,
            pay_time__isnull=False,
            payment__gt=0,
            coin_paid=0,
            budget_paid=0
        )
        date_set = set()

        print 'recalc_trade_count=',sts.count()
        for st in sts.iterator():
            st.budget_paid = st.pay_cash
            st.pay_cash = 0
            st.save()
            date_set.add(st.pay_time.date())
            print 'tid=', st.tid

        print 'recalc_daystats_date_count', len(date_set)
        for dt in sorted(list(date_set)):
            task_Push_Sales_To_DailyStat(dt)
            print 'calc date= %s'%dt

