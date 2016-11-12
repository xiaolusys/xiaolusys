from __future__ import absolute_import

import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
from global_setup import setup_djagno_environ
setup_djagno_environ()

from django.conf import settings  # noqa

app = Celery('shopmanager')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
CLOSE_CELERY = False