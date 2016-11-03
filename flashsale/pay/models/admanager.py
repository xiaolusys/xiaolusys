# encoding=utf8
from django.db import models
from .base import BaseModel


class ADManager(BaseModel):
    title = models.CharField(max_length=512, verbose_name=u'广告标题')
    image = models.CharField(max_length=512, blank=True, verbose_name=u'广告图片')
    url = models.CharField(max_length=512, verbose_name=u'跳转链接')
    status = models.BooleanField(default=True, verbose_name=u"使用")

    class Meta:
        db_table = 'flashsale_admanager'
        app_label = 'pay'
        verbose_name = u'广告系统'
        verbose_name_plural = u'广告投放系统'
