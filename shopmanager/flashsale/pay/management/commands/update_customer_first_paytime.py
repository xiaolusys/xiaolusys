# encoding=utf8
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db.models import Min

from flashsale.pay.models.user import Customer
from flashsale.pay.models.trade import SaleTrade


class Command(BaseCommand):
    def handle(self, *args, **options):
        start_day = datetime(2015, 1, 1)

        items = SaleTrade.objects.filter(pay_time__isnull=False, pay_time__gt=start_day).values('buyer_id').annotate(min_pay_time=Min('pay_time'))
        total_count = items.count()

        for i, item in enumerate(items):
            pay_time = item['min_pay_time']
            buyer_id = item['buyer_id']

            if i % 1000 == 0:
                print '%s/%s' % (i, total_count), buyer_id

            customer = Customer.objects.filter(id=buyer_id).first()
            if customer:
                customer.first_paytime = pay_time
                customer.save()
