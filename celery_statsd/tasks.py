# coding: utf8
from __future__ import absolute_import, unicode_literals

import requests
from requests.auth import HTTPBasicAuth

from shopmanager import celery_app as app
from .conf import FLOWER_QUEUE_LENGTH_API, FLOWER_USERNAME, FLOWER_PASSWORD

@app.task
def task_celery_queue_message_statsd():

    from django_statsd.clients import statsd
    resp = requests.get(FLOWER_QUEUE_LENGTH_API,
                              auth=HTTPBasicAuth(FLOWER_USERNAME, FLOWER_PASSWORD))
    queue_stats = resp.json().get('active_queues',[])
    for stat in queue_stats:
        statsd.gauge('celery.queue.%s'% stat['name'], stat['messages'])
