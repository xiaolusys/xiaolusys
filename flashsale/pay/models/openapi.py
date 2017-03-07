# encoding=utf8
from __future__ import unicode_literals

from django.db import models
from .base import BaseModel


class OpenAPI(BaseModel):
    app_id = models.CharField(max_length=16, db_index=True, unique=True, verbose_name=u'应用 ID')
    app_secret = models.CharField(max_length=32, verbose_name=u'应用 SECRET')
    name = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'应用名称')

    class Meta:
        db_table = 'flashsale_openapi'
        app_label = 'pay'
