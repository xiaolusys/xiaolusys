# -*- coding:utf-8 -*-.
from __future__ import unicode_literals

from django.db import models


# Create your models here.

class PaintAccount(models.Model):
    account_name = models.CharField(max_length=64, unique=True, blank=True, verbose_name=u'账号')
    customer_id = models.IntegerField(default=0, verbose_name=u'来源订单号')

    password = models.CharField(max_length=64, blank=True, verbose_name=u'密码')
    mobile = models.CharField(max_length=64, unique=True, blank=True, verbose_name=u'手机号')
    province = models.CharField(max_length=64, blank=True, verbose_name=u'省')
    street_addr = models.CharField(max_length=128, blank=True, verbose_name=u'街道地址')

    is_tb = models.IntegerField(default=0, verbose_name=u'淘宝帐号')
    is_jd = models.IntegerField(default=0, verbose_name=u'京东帐号')
    is_wx = models.IntegerField(default=0, verbose_name=u'微信帐号')

    creater_id = models.IntegerField(default=0, verbose_name=u'创建者ID')
    owner_id = models.IntegerField(default=0, verbose_name=u'拥有者ID')

    status = models.IntegerField(default=0, verbose_name=u'帐号状态')

    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改日期')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u'创建日期')

    class Meta:
        db_table = 'games_paint_paintaccount'
        app_label = 'paint'
        verbose_name = u'Paint帐号'
        verbose_name_plural = u'Paint帐号列表'

    def __unicode__(self):
        return '%s' % self.account_name
