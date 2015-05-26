# -*- coding:utf-8 -*-
__author__ = 'yann'
from django.db import models
from django.contrib.auth.models import User as DjangoUser

from shopback.base.fields import BigIntegerForeignKey


class MyGroup(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        db_table = 'suplychain_flashsale_mygroup'
        verbose_name = u'订货用户分组表'
        verbose_name_plural = u'订货用户分组表'

    def __unicode__(self):
        return self.name


class MyUser(models.Model):
    user = BigIntegerForeignKey(DjangoUser, unique=True, verbose_name=u'原始用户')
    group = BigIntegerForeignKey(MyGroup, verbose_name=u'组', blank=True)

    class Meta:
        db_table = 'suplychain_flashsale_myuser'
        verbose_name = u'订货用户表'
        verbose_name_plural = u'订货用户表'

    def __unicode__(self):
        return self.user.username

