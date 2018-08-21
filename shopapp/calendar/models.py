# -*- coding:utf8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

EVENT_TYPE = (
    ('peroid', u'周期任务'),
    ('temp', u'一次任务'),
)

EVENT_STATUS = (
    ('normal', u'正常'),
    ('cancel', u'取消'),
)


class StaffEvent(models.Model):
    """ 员工任务计划 """

    executor = models.ForeignKey(User, null=True, default=None, related_name='staff_execute_events', verbose_name='执行者')
    creator = models.ForeignKey(User, null=True, default=None, related_name='staff_create_events', verbose_name='创建者')

    start = models.DateTimeField(null=False, verbose_name='开始日期')
    end = models.DateTimeField(null=True, blank=True, verbose_name='结束日期')

    interval_day = models.IntegerField(default=0, verbose_name='间隔天数')

    title = models.CharField(max_length=1000, blank=True, verbose_name='内容')
    type = models.CharField(max_length=1000, blank=True, choices=EVENT_TYPE, verbose_name='类型')

    created = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name='创建日期')
    modified = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name='修改日期')

    is_finished = models.BooleanField(default=False, verbose_name='已完成')

    status = models.CharField(max_length=10, default='normal', choices=EVENT_STATUS, verbose_name='状态')

    class Meta:
        db_table = 'shop_calendar_staffevent'
        app_label = 'calendar'
        verbose_name = u'事件'
        verbose_name_plural = u'事件列表'

    def __unicode__(self):
        return '<%d,%s,%s>' % (self.id, self.executor.username, self.creator.username)
