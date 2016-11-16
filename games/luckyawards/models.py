# encoding:utf-8
from __future__ import unicode_literals

from django.db import models
from django.conf import settings


class Joiner(models.Model):
    name = models.CharField(max_length=64, verbose_name=u'姓名')
    thumbnail = models.ImageField(upload_to='picture/luckyawards/', max_length=256, verbose_name=u'照片')
    born_at = models.DateField(blank=True, null=True, verbose_name=u'出生年月')
    addresss = models.CharField(max_length=64, blank=True, verbose_name=u'地址')
    descript = models.CharField(max_length=128, blank=True, verbose_name=u'说明')

    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改日期')

    is_active = models.BooleanField(default=True, verbose_name=u'是否有效')

    class Meta:
        db_table = 'game_joiner'
        app_label = 'luckyawards'
        verbose_name = u'活动抽奖'
        verbose_name_plural = u'活动抽奖人员列表'

