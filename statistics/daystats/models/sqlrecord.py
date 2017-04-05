# coding: utf8
from __future__ import absolute_import, unicode_literals

import hashlib
import datetime
from django.db import models
from core.fields import JSONCharMyField
from core.models import BaseModel

class DailySqlRecord(BaseModel):
    """ 查询sql记录保存 """

    query_data = JSONCharMyField(max_length=5000, verbose_name=u'查询条件')
    uni_key = models.CharField(max_length=32, blank=False, unique=True, verbose_name=u'唯一标识')

    status = models.BooleanField(default=True, verbose_name=u'是否使用')

    class Meta:
        db_table = 'flashsale_daily_sqlrecord'
        app_label = 'daystats'
        verbose_name = u'每日统计/查询sql记录'
        verbose_name_plural = u'每日统计/查询sql记录'

    @classmethod
    def gen_unikey(cls, key_string):
        return hashlib.md5(key_string).hexdigest()

    @classmethod
    def normal_records(cls):
        return DailySqlRecord.objects.filter(status=True)

    def set_invalid(self):
        self.status = False