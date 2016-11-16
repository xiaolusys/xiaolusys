# -*- coding:utf8 -*-
from __future__ import unicode_literals

import json
import datetime
from django.db import models
from shopback.signals import user_logged_in
import logging

logger = logging.getLogger('django.request')
DEFAULT_GROUP_NAME = 'default'


class ValidUserManager(models.Manager):
    def get_queryset(self):
        return super(ValidUserManager, self).get_queryset().filter(is_valid=True)


class TmcMessage(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.BigIntegerField(db_index=True, verbose_name=u'店铺ID')

    topic = models.CharField(max_length=128, blank=True, verbose_name=u'消息主题')
    pub_app_key = models.CharField(max_length=64, blank=True, verbose_name=u'发布者APPKEY')

    pub_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'发布时间')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'入库时间')

    content = models.TextField(max_length=2000, blank=True, verbose_name=u'消息内容')

    is_exec = models.BooleanField(default=False, verbose_name=u'执行')

    class Meta:
        db_table = 'shop_tmcnotify_message'
        app_label = 'tmcnotify'
        verbose_name = u'服务消息'
        verbose_name_plural = u'服务消息列表'

    def __unicode__(self):
        return '<%d,%s>' % (self.id, self.topic)


class TmcUser(models.Model):
    user_id = models.BigIntegerField(db_index=True, verbose_name=u'店铺ID')

    user_nick = models.CharField(max_length=64, blank=True, verbose_name=u'用户昵称')

    modified = models.DateTimeField(null=True, blank=True, verbose_name=u'修改时间')
    created = models.DateTimeField(null=True, blank=True, verbose_name=u'创建时间')

    topics = models.TextField(max_length=2500, blank=True, verbose_name=u'消息主题')
    group_name = models.CharField(max_length=64, blank=True, default=DEFAULT_GROUP_NAME, verbose_name=u'消息群组')
    quantity = models.IntegerField(default=100, verbose_name=u'消息数量')

    is_valid = models.BooleanField(default=False, verbose_name=u'是否有效')

    is_primary = models.BooleanField(default=False, verbose_name=u'主用户')

    valid_users = ValidUserManager()

    class Meta:
        db_table = 'shop_tmcnotify_user'
        app_label = 'tmcnotify'
        verbose_name = u'消息服务用户'
        verbose_name_plural = u'消息服务用户列表'

    def __unicode__(self):
        return '<%d,%s>' % (self.user_id, self.user_nick)

    @property
    def topic_set(self):
        return set([s.strip() for s in self.topics.split(',')])


def createTmcUser(sender, user, *args, **kwargs):
    logger.debug('debug createTmcUser receiver:%s' % sender)
    top_params = kwargs.get('top_parameters', '{}')
    top_params = isinstance(top_params, dict) and top_params or json.dumps(top_params)
    visitor_id = top_params and top_params.get('taobao_user_id') or None
    if not visitor_id:
        return
    visitor_nick = top_params and top_params.get('taobao_user_nick') or ''
    tmc_user, state = TmcUser.valid_users.get_or_create(
        user_id=visitor_id)
    tmc_user.user_nick = visitor_nick
    tmc_user.save()


user_logged_in.connect(createTmcUser,
                       sender='taobao',
                       dispatch_uid='create_tmc_user')
