# -*- coding:utf-8 -*-
from django.db import models


class ClickCount(models.Model):
    number = models.IntegerField(verbose_name=u'数字')
    name = models.CharField(max_length=32, db_index=True, verbose_name=u'名字')
    nop = models.IntegerField(verbose_name=u'人数')
    frequency = models.IntegerField(verbose_name=u'次数')
    date = models.DateTimeField(verbose_name=u'日期')
    write_time = models.DateTimeField(auto_now_add=True, verbose_name=u'写入时间')
    administrator = models.IntegerField(db_index=True, verbose_name=u'管理员')

    class Meta:
        db_table = 'suplychain_flashsale_clickcount'
        verbose_name = u'点击统计表'
        verbose_name_plural = u'单击统计表列表'

    def __unicode__(self):
        return self.name