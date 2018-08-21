# coding: utf-8
import datetime

from optparse import make_option
import traceback

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from shopback.items.models import ProductSchedule


class Command(BaseCommand):
    # 28182, 123
    def handle(self, *args, **kwargs):
        from shopback.items.local_cache import rebeta_schema_cache
        now = datetime.datetime.now()
        today = now.date()
        hour = int(now.strftime('%H'))

        print rebeta_schema_cache.schemas
        """
        p = ProductSchedule(product_id=28182, creator='123', onshelf_datetime=now, offshelf_datetime=now, onshelf_date=today, offshelf_date=today,
                            onshelf_hour=hour, offshelf_hour=hour, schedule_type=1)
        p.save()
        """
        print ProductSchedule.objects.select_related().filter(pk=1).query
