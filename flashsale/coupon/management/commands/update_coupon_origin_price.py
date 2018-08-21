# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from flashsale.coupon.models import UserCoupon
from flashsale.pay.models import SaleOrder

class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('start_date', nargs='+', type=str)

    def handle(self, *args, **options):
        start_date = options.get('start_date')[0]

        usercoupons = UserCoupon.objects.get_origin_payment_boutique_coupons()\
            .filter(created__gt=start_date).only('id','uniq_id','extras')
        print 'update total: ', usercoupons.count()

        cnt = 0
        for cp in usercoupons.iterator():
            saleorder_id = cp.uniq_id.split('_')[2]
            saleorder = SaleOrder.objects.get(id=saleorder_id)

            cp.extras['origin_price'] = int(saleorder.payment * 100) / saleorder.num
            cp.save(update_fields=['extras'])

            cnt += 1
            if cnt % 500 == 0: print cnt


