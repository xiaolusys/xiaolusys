# -*- encoding:utf8 -*-
from __future__ import unicode_literals

from django.db import models

TASK_CREATED = 'CREATED'
TASK_ASYNCOK = 'ASYNCOK'
TASK_ASYNCCOMPLETE = 'ASYNCCOMPLETE'
TASK_DOWNLOAD = 'DOWNLOAD'
TASK_SUCCESS = 'SUCCESS'
TASK_INVALID = 'INVALID'

TAOBAO_ASYNC_TASK_STATUS = (
    (TASK_CREATED, '任务已创建'),
    (TASK_ASYNCOK, '淘宝异步任务请求成功'),
    (TASK_ASYNCCOMPLETE, '淘宝异步任务完成'),
    (TASK_DOWNLOAD, '异步任务结果已下载本地'),
    (TASK_SUCCESS, '任务已完成'),
    (TASK_INVALID, '任务已作废'),
)


class TaobaoAsyncTaskModel(models.Model):
    # 淘宝异步任务处理MODEL
    task_id = models.AutoField(primary_key=True, verbose_name=u'任务ID')
    task = models.TextField(max_length=256, blank=True, verbose_name=u'任务标题')

    top_task_id = models.CharField(max_length=128, db_index=True, blank=True, verbose_name=u'淘宝任务ID')
    user_id = models.CharField(max_length=64, blank=True, verbose_name=u'用户ID')

    result = models.TextField(max_length=2000, blank=True, verbose_name=u'任务结果')
    fetch_time = models.DateField(null=True, blank=True, verbose_name=u'获取时间')
    file_path_to = models.TextField(max_length=256, blank=True, verbose_name=u'结果存放路径')

    create = models.DateField(auto_now=True, verbose_name=u'创建时间')
    modified = models.DateField(auto_now_add=True, verbose_name=u'修改时间')
    status = models.CharField(max_length=32, choices=TAOBAO_ASYNC_TASK_STATUS, default=TASK_CREATED, verbose_name=u'状态')

    params = models.CharField(max_length=1000, blank=True, null=True, verbose_name=u'任务参数')

    class Meta:
        db_table = 'shop_asynctask_taobao'
        app_label = 'asynctask'
        verbose_name = u'淘宝异步任务'
        verbose_name_plural = u'淘宝异步任务列表'

    def __unicode__(self):
        return u'<TaobaoAsyncTaskModel:%d,%s>' % (self.task_id, self.task)


class PrintAsyncTaskModel(models.Model):
    TASK_CREATED = 0
    TASK_SUCCESS = 1
    TASK_INVALID = -1
    PRINT_TASK_STATUS = (
        (TASK_CREATED, '任务已创建'),
        (TASK_SUCCESS, '任务已完成'),
        (TASK_INVALID, '任务失败'),
    )

    INVOICE = 0
    EXPRESS = 1
    PRINT_TYPE = ((INVOICE, u'打印发货单'),
                  (EXPRESS, u'打印物流单'),)

    task_id = models.AutoField(primary_key=True, verbose_name=u'任务ID')
    task_type = models.IntegerField(choices=PRINT_TASK_STATUS, default=TASK_CREATED, verbose_name=u'任务类型')

    operator = models.CharField(max_length=16, db_index=True, blank=True, verbose_name=u'操作员')
    file_path_to = models.CharField(max_length=256, blank=True, verbose_name=u'结果存放路径')

    created = models.DateField(auto_now=True, verbose_name=u'创建日期')
    modified = models.DateField(auto_now_add=True, verbose_name=u'修改日期')
    status = models.IntegerField(choices=PRINT_TASK_STATUS, default=TASK_CREATED, verbose_name=u'任务状态')

    params = models.TextField(max_length=5000, blank=True, null=True, verbose_name=u'任务参数')

    class Meta:
        db_table = 'shop_asynctask_print'
        app_label = 'asynctask'
        verbose_name = u'异步打印任务'
        verbose_name_plural = u'异步打印任务列表'

    def __unicode__(self):
        return u'<PrintAsyncTask:%d,%s>' % (self.task_id, self.get_task_type_display())
