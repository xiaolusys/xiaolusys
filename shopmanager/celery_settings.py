from __future__ import absolute_import

import os
import django
from celery import Celery

# set the default Django settings module for the 'celery' program.
from global_setup import setup_djagno_environ
setup_djagno_environ()
django.setup()

app = Celery('shopmanager')
# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

from . import task_settings as ts

app.conf.accept_content = ts.CELERY_ACCEPT_CONTENT
app.conf.task_serializer = ts.CELERY_TASK_SERIALIZER

app.conf.task_queues = ts.CELERY_QUEUES
app.conf.task_default_queue = ts.CELERY_DEFAULT_QUEUE
app.conf.task_default_exchange = ts.CELERY_DEFAULT_EXCHANGE
app.conf.task_default_routing_key = ts.CELERY_DEFAULT_ROUTING_KEY

app.conf.task_routes = ts.CELERY_ROUTES
app.conf.beat_schedule = ts.CELERYBEAT_SCHEDULE



