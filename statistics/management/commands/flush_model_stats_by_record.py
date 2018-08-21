# coding=utf-8
import datetime
from django.core.management.base import BaseCommand
from statistics.models import SaleOrderStatsRecord


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('date_from', nargs='+', type=str,
                            help='assign a date_from to filter that date sal trade.')
        parser.add_argument('date_to', nargs='+', type=str,
                            help='assign a date_to to filter that date sal trade.')
        parser.add_argument('review_days', nargs='+', type=int,
                            help='assign a review_days to task review_days.')

    def handle(self, *args, **options):
        date_froms = options.get('date_from')
        date_tos = options.get('date_to')
        review_days = options.get('review_days')

        if date_froms and date_tos:
            date_from = date_froms[0]
            date_to = date_tos[0]
            review_days = review_days[0]

            records = SaleOrderStatsRecord.objects.filter(pay_time__gte=date_from, pay_time__lt=date_to)
            print "date_from :%s date_to :%s record count is %s" % (date_from, date_to, records.count())
            from statistics.tasks import task_statsrecord_update_model_stats

            for record in records:
                task_statsrecord_update_model_stats.delay(record, review_days=review_days)
