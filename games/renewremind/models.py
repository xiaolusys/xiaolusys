# coding=utf-8
from django.db import models
from core.models import BaseModel


class RenewRemind(BaseModel):
    project_name = models.CharField(max_length=128, verbose_name=u'项目名称')
    service_provider = models.CharField(max_length=128, verbose_name=u'提供商')
    provider_phone = models.CharField(max_length=11, blank=True, verbose_name=u'服务供应商电话')
    start_service_time = models.DateTimeField(blank=True, verbose_name=u'开始服务时间')
    expire_time = models.DateTimeField(verbose_name=u'服务到期时间')
    describe = models.TextField(max_length=1024, blank=True, verbose_name=u'服务描述')
    amount = models.FloatField(verbose_name=u'续费金额')
    principal = models.CharField(max_length=32, verbose_name=u'主要负责人')
    principal_phone = models.CharField(max_length=11, verbose_name=u'主要负责人手机')
    principal2_phone = models.CharField(max_length=11, verbose_name=u'第2负责人手机')
    principal3_phone = models.CharField(max_length=11, verbose_name=u'第3负责人手机')
    is_trace = models.BooleanField(default=True, db_index=True, verbose_name=u'是否追踪')

    class Meta:
        app_label = 'monitor'
        db_table = 'extrafunc_service_remind'
        verbose_name = u'系统服务/续费提醒记录表'
        verbose_name_plural = u'系统服务/续费提醒记录列表'

