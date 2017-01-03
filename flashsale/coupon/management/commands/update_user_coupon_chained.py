# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from flashsale.coupon.models import UserCoupon

class Command(BaseCommand):
    def handle(self, *args, **options):
        ucs = UserCoupon.objects.filter(coupon_type=UserCoupon.TYPE_TRANSFER).only('id','extras')
        cnt = 0
        for uc in ucs:
            chain = uc.extras.get('chain')
            if chain:
                uc.is_chained = True
                uc.save(update_fields=['is_chained'])
                cnt += 1
                if cnt % 1000 == 0: print cnt

        print 'chained total:', cnt

