# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import models

class JimayAgent(models.Model):

    nick = models.CharField(max_length=32, db_index=True, blank=True, verbose_name='昵称')

    name = models.CharField(max_length=32, db_index=True, blank=True, verbose_name='姓名')
    idcard_no = models.CharField(max_length=18, blank=True, verbose_name='身份证号')

    weixin = models.CharField(max_length=24, db_index=True, blank=True, verbose_name='微信')
    mobile = models.CharField(max_length=11, unique=True, blank=True, verbose_name='手机')
    level = models.IntegerField(default=0, db_index=True, verbose_name='级别')

    parent_agent_id = models.IntegerField(default=0, db_index=True, verbose_name='父级代理ID')

    address = models.CharField(max_length=128, blank=True, verbose_name='收货地址')

    certification = models.CharField(max_length=256, blank=True, verbose_name='证书地址', help_text='暂不使用链接')

    created = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name='修改日期')

    class Meta:
        db_table = 'jimay_agent'
        app_label = 'jimay'
        verbose_name = '己美医学/特约代理'
        verbose_name_plural = '己美医学/特约代理'

    def __unicode__(self):
        return '%s,%s' % (self.id, self.name)