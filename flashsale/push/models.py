# coding=utf-8
from __future__ import unicode_literals

from django.db import models

from models_message import PushMsgTpl



class PushTopic(models.Model):
    STATUSES = (
        (0, u'无效'),
        (1, u'有效')
    )

    class Meta:
        db_table = 'push_topics'
        index_together = [('device_id', 'platform', 'cat')]
        app_label = 'push'
        verbose_name = u'小米推送标签'
        verbose_name_plural = u'小米推送标签'

    id = models.AutoField(primary_key=True, verbose_name=u'主键')
    customer = models.ForeignKey('pay.Customer', null=True, blank=True, verbose_name=u'用户')
    cat = models.PositiveIntegerField(blank=True, default=0, verbose_name=u'分类')
    platform = models.CharField(max_length=16, verbose_name=u'平台')
    regid = models.CharField(max_length=512, verbose_name=u'小米regid')
    ios_token = models.CharField(max_length=128, blank=True, verbose_name=u'ios系统token')
    device_id = models.CharField(max_length=48, blank=True, verbose_name=u'设备ID')
    topic = models.CharField(max_length=128, blank=True, verbose_name=u'推送标签')
    update_time = models.FloatField(null=True, blank=True, verbose_name=u'更新时间')
    status = models.SmallIntegerField(choices=STATUSES, default=1, verbose_name=u'状态')
