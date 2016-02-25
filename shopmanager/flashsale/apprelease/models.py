# coding=utf-8
from django.db import models
from core.models import BaseModel


class AppRelease(BaseModel):
    """
    存储release过的客户端地址，方便下载页面调用，和后台及时更换
    """

    class Meta:
        db_table = 'flashsale_app_release'
        verbose_name = u'特卖/App下载版本表'
        verbose_name_plural = u'特卖/App下载版本列表'

    VALID = 0
    INVALID = 1
    RELEASE_STATUS = ((VALID, u'有效'), (INVALID, u'无效'))
    download_link = models.CharField(max_length=512, verbose_name=u'存储链接地址')
    version = models.CharField(max_length=128, db_index=True, verbose_name=u'客户端版本号')
    status = models.IntegerField(default=0, verbose_name=u'投放状态', db_index=True, choices=RELEASE_STATUS)
    release_time = models.DateTimeField(blank=True, null=True, verbose_name=u'投放时间')
    memo = models.TextField(max_length=1024, blank=True, null=True, verbose_name=u'备注')




