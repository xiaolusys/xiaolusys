# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
import requests
from requests.auth import HTTPBasicAuth

from django.conf import settings

from shopmanager import celery_app as app
from .conf import FLOWER_QUEUE_LENGTH_API, FLOWER_USERNAME, FLOWER_PASSWORD

import logging
logger = logging.getLogger(__name__)

@app.task
def task_celery_queue_message_statsd():

    from django_statsd.clients import statsd
    resp = requests.get(FLOWER_QUEUE_LENGTH_API,
                              auth=HTTPBasicAuth(FLOWER_USERNAME, FLOWER_PASSWORD))

    # if 502 means the flower server are restarting
    if resp.status_code == 502:
        return

    queue_stats = resp.json().get('active_queues',[])
    for stat in queue_stats:
        statsd.gauge('celery.queue.%s'% stat['name'], stat['messages'])


@app.task()
def task_periodic_flush_elasticsearch_logging(remain_days=7):
    today = datetime.datetime.now()
    try:
        for i in (remain_days, 15):
            dt = today - datetime.timedelta(days=i)
            req_url = 'http://{}/{}'.format(settings.ELASTICSEARCH_LOGGING_HOST, '-' + dt.strftime('%Y.%m.%d'))
            resp = requests.delete(req_url)
            if resp.status_code > 400 and resp.status_code != 404:
                logger.error('delete-es-logging-error:%s, %s' % (req_url, resp.text))

            req_url1 = 'http://{}/{}'.format(settings.ELASTICSEARCH_LOGGING_HOST, 'logstash-' + dt.strftime('%Y.%m.%d'))
            resp = requests.delete(req_url1)
            if resp.status_code > 400 and resp.status_code != 404:
                logger.error('delete-es-logging-error:%s, %s' % (req_url, resp.text))
    except Exception, exc:
        logger.error(str(exc), exc_info=True)