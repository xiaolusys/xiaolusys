# -*- coding:utf8 -*-
import time
import datetime
import json
from celery.task import task
from celery import Task
from django.conf import settings

from common.utils import update_model_fields
