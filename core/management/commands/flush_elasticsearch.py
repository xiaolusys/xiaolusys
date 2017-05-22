# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from django.conf import settings
import datetime
import requests

import logging
logger = logging.getLogger(__name__)

ELASTICSEARCH_LOGGING_HOST = settings.E

class Command(BaseCommand):

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('remain_days', nargs='+', type=str)

    def handle(self, *args, **options):

        remain_days = int(options.get('remain_days')[0])

        today = datetime.datetime.now()
        try:
            for i in (remain_days, 10):
                dt = today - datetime.timedelta(days=i)
                req_url = 'http://{}/{}'.format(ELASTICSEARCH_LOGGING_HOST, '-' + dt.strftime('%Y.%m.%d'))
                resp = requests.delete(req_url)
                if resp.status_code > 400 and resp.status_code != 404:
                    logger.error('delete-es-logging-error:%s, %s' % (req_url, resp.text))
        except Exception, exc:
            logger.error(str(exc), exc_info=True)

