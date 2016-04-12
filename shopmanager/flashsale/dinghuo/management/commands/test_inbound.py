# coding: utf-8

import datetime
from operator import itemgetter
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand

from flashsale.dinghuo.models import InBound, InBoundDetail, OrderDetail, OrderDetailInBoundDetail


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-d', '--delete', dest='is_del', action='store_true', default=False),
    )

    def handle(self, *args, **kwargs):
        is_del = kwargs['is_del']
        if is_del:
            self.delete_all()

    @classmethod
    def delete_all(cls):
        OrderDetailInBoundDetail.objects.all().delete()
        InBoundDetail.objects.all().delete()
        InBound.objects.all().delete()

        for orderdetail in OrderDetail.objects.filter(orderlist_id=51):
            orderdetail.arrival_quantity = 0
            orderdetail.inferior_quantity = 0
            orderdetail.save()
