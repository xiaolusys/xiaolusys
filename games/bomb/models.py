# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class WeixinBomb(models.Model):
    name = models.CharField(max_length=64, unique=True, blank=True, verbose_name=u'微信号')

    contact = models.CharField(max_length=32, blank=True, verbose_name=u'联系人')
    phone = models.CharField(max_length=32, blank=True, verbose_name=u'电话')
    mobile = models.CharField(max_length=16, blank=True, verbose_name=u'手机')
    email = models.CharField(max_length=64, blank=True, verbose_name=u'邮箱')
    qq = models.CharField(max_length=16, blank=True, verbose_name=u'QQ号')

    numfans = models.IntegerField(default=0, verbose_name="粉丝数")
    region = models.CharField(max_length=16, blank=True, verbose_name=u"地区")
    category = models.CharField(max_length=16, blank=True, verbose_name=u"类别")
    price = models.IntegerField(default=0, verbose_name=u"标注价")

    coverage = models.IntegerField(default=0, verbose_name=u"覆盖估计")

    creator = models.ForeignKey(User, null=True, related_name='bombers', verbose_name=u'接洽人')

    payinfo = models.CharField(max_length=128, blank=True, verbose_name=u'支付信息')
    memo = models.TextField(blank=True, verbose_name=u'备注')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'games_bomb_weixinbomb'
        app_label = 'bomb'
        verbose_name = u'微信bomb'
        verbose_name_plural = u'微信bomb列表'

    def __unicode__(self):
        return self.name
