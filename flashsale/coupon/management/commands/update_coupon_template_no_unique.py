# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from flashsale.coupon.models import CouponTemplate

class Command(BaseCommand):
    def handle(self, *args, **options):
        cpts = CouponTemplate.objects.all()
        for cpt in cpts:
            date = cpt.created.date()
            cpt.template_no = CouponTemplate.gen_default_template_no(date)
            cpt.save(update_fields=['template_no'])
            print cpt, cpt.template_no