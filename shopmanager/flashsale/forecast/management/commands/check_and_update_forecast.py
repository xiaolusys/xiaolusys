# coding: utf-8

import datetime
from django.core.management.base import BaseCommand

from flashsale.forecast.models import ForecastInbound

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        logger.info('check and update forecast start ...')
        fbs = ForecastInbound.objects.filter(status__in=(ForecastInbound.ST_DRAFT,ForecastInbound.ST_APPROVED))
        order_count = {}
        for fb in fbs:
            ods = fb.relate_order_set.all()
            for od in ods:
                order_count.setdefault(od.sys_status,0)
                order_count[od.sys_status] += 1
        logger.info('forecast stats count: %s'% order_count)

        timeout_close = 0
        fbs = ForecastInbound.objects.filter(status=ForecastInbound.ST_DRAFT)
        for fb in fbs:
            ods = fb.relate_order_set.exclude(sys_status='finished')
            if not ods.exists():
                fb.status = ForecastInbound.ST_TIMEOUT
                fb.save(update_fields=['status'])
                timeout_close += 1
        logger.info('forecast timeout count: %s' % timeout_close)

        fbs = ForecastInbound.objects.filter(status__in=(ForecastInbound.ST_DRAFT,ForecastInbound.ST_APPROVED))
        for fb in fbs:
            ods = fb.relate_order_set.all()
            for od in ods:
                if od.sys_status == 'draft':
                    logger.info('forecast except:%s' % ','.join([str(fb.id), str(od.id), od.get_status_display(), od.get_stage_display()]))
                    od.save()