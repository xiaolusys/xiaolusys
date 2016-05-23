# coding=utf-8
from django.core.management.base import BaseCommand
from statistics.tasks import task_update_sale_order_stats_record


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('date_from', nargs='+', type=str,
                            help='assign a date_from to filter that date sal trade.')
        parser.add_argument('date_to', nargs='+', type=str,
                            help='assign a date_to to filter that date sal trade.')

    def handle(self, *args, **options):
        date_froms = options.get('date_from')
        date_tos = options.get('date_to')
        if date_froms and date_tos:
            date_from = date_froms[0]
            date_to = date_tos[0]
            print "date_from :%s date_to :%s" % (date_from, date_to)
            from flashsale.pay.models import SaleOrder
            # orders = SaleOrder.objects.filter(created__gte='2016-4-15 00:00:00', created__lte='2016-4-16 23:59:59')
            orders = SaleOrder.objects.filter(created__gte=date_from, created__lte=date_to).order_by('pay_time')
            for order in orders:
                task_update_sale_order_stats_record(order)
