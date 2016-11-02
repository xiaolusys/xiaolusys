# -*- encoding:utf8 -*-
import types
import json
from django.conf import settings
from django.core.cache import cache
from celery.task import task
from celery.registry import tasks
from celery.app.task import BaseTask
