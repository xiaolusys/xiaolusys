# coding=utf-8
import datetime
from django.core.management.base import BaseCommand
from common.utils import update_model_fields
from statistics.models import SaleOrderStatsRecord


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('date_from', nargs='+', type=str,
                            help='assign a date_from to filter that date sal trade.')
        parser.add_argument('date_to', nargs='+', type=str,
                            help='assign a date_to to filter that date sal trade.')

    def handle(self, *args, **options):
        """
        更新（不能使用保存） 交易统计明细列表 中的pay_time字段
        """
        date_froms = options.get('date_from')
        date_tos = options.get('date_to')

        if date_froms and date_tos:
            date_from = date_froms[0]
            date_to = date_tos[0]
            from flashsale.pay.models import SaleOrder

            orders = SaleOrder.objects.filter(created__gte=date_from, created__lte=date_to)
            print "orders count is %s:" % orders.count()
            records = SaleOrderStatsRecord.objects.all()
            for order in orders:
                record = records.filter(oid=order.oid).first()
                if record:
                    record.pay_time = order.pay_time if order.pay_time else order.created
                    update_model_fields(record, ['pay_time'])
                else:
                    print "record not found order id %s" % order.id
