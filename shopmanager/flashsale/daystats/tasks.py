# -*- encoding:utf8 -*-
import datetime
from django.db.models import F
from celery.task import task

from .models import DailyStat

import logging

__author__ = 'yann'

logger = logging.getLogger('celery.handler')