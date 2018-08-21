# -*- coding:utf8 -*-
from __future__ import unicode_literals
from django.db import models

LISTING_TYPE = 'listing'
DELISTING_TYPE = 'delisting'
TASK_TYPE = (
    (LISTING_TYPE, '上架'),
    (DELISTING_TYPE, '下架')
)

UNEXECUTE = 'unexecute'
EXECERROR = 'execerror'
SUCCESS = 'success'
DELETE = 'delete'
UNSCHEDULED = 'unscheduled'
TASK_STATUS = (
    (UNEXECUTE, '未执行'),
    (EXECERROR, '执行出错'),
    (SUCCESS, '成功'),
    (DELETE, '删除'),
    (UNSCHEDULED, '未设定')
)


class TimeSlots(models.Model):
    timeslot = models.IntegerField(primary_key=True)

    class Meta:
        db_table = 'shop_autolist_timeslot'
        app_label = 'autolist'
        ordering = ['timeslot']
        verbose_name = u'上架时间轴'
        verbose_name_plural = u'上架时间轴'

    @property
    def hour(self):
        return self.timeslot / 100

    @property
    def minute(self):
        return self.timeslot % 100


class ItemListTask(models.Model):
    num_iid = models.CharField(primary_key=True, max_length=64)
    user_id = models.CharField(max_length=32, blank=True)

    nick = models.CharField(max_length=32, blank=True)
    title = models.CharField(max_length=128, blank=True)
    num = models.IntegerField()

    list_weekday = models.IntegerField()
    list_time = models.CharField(max_length=8)

    task_type = models.CharField(max_length=10, choices=TASK_TYPE, blank=True,
                                 default=LISTING_TYPE)  # listing, delisting
    created_at = models.DateTimeField(null=True, blank=True, auto_now=True)

    status = models.CharField(max_length=10, choices=TASK_STATUS,
                              default=UNEXECUTE)  # unexecute,execerror,success,delete

    class Meta:
        db_table = 'shop_autolist_itemlisttask'
        app_label = 'autolist'
        verbose_name = u'上架任务'
        verbose_name_plural = u'上架任务列表'

    @property
    def hour(self):
        return int(self.list_time.split(':')[0])

    @property
    def minute(self):
        return int(self.list_time.split(':')[1])


class Logs(models.Model):
    num_iid = models.CharField(max_length=64)
    cat_id = models.CharField(max_length=64)
    cat_name = models.CharField(max_length=64)
    outer_id = models.CharField(max_length=64)
    title = models.CharField(max_length=128)
    pic_url = models.URLField()

    list_weekday = models.IntegerField()
    list_time = models.CharField(max_length=8)
    num = models.IntegerField()

    task_type = models.CharField(max_length=10, blank=True)
    execute_time = models.DateTimeField(null=True, blank=True, auto_now_add=True)

    status = models.CharField(max_length=20)  # unexec

    class Meta:
        db_table = 'shop_autolist_logs'
        app_label = 'autolist'
        verbose_name = u'上架任务日志'
        verbose_name_plural = u'任务日志'
