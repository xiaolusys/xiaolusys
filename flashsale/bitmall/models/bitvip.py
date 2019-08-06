# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import datetime
from random import choice

from django.conf import settings
from django.db import models, transaction

from core.models import BaseModel

class BitVIP(BaseModel):

    NONE = 'none'
    PROFILE = 'profile'
    PAY = 'pay'
    PASS = 'pass'
    PROGRESS_CHOICES = (
        (NONE, u'未申请'),
        (PROFILE, u'填写资料'),
        (PAY, u'支付押金'),
        (PASS, u'申请成功'),
    )

    user = models.OneToOneField('auth.User', related_name='bit_vip', verbose_name=u'原始用户')

    parent = models.ForeignKey('self', null=True, verbose_name=u'邀请人')

    progress = models.CharField(max_length=8, blank=True, db_index=True, choices=PROGRESS_CHOICES,
                                default=NONE, verbose_name=u'申请进度')

    class Meta:
        db_table = 'bitmall_vip'
        app_label = 'bitmall'
        verbose_name = u'比特商城用户'
        verbose_name_plural = u'比特商城用户列表'

    def __unicode__(self):
        return '%s' % self.id


    @property
    def name(self):
        return self.user.customer.nick

    @property
    def mobile(self):
        return self.user.customer.mobile