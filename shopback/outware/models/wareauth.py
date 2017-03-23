# coding: utf8
from __future__ import absolute_import, unicode_literals

import random
import hashlib
import datetime
from django.db import models

# from django.db import models
from core.fields import JSONCharMyField
from .base import BaseWareModel

import logging
logger = logging.getLogger(__name__)

def gen_default_appid():
    return 'app{date}{randchar}'.format(
        date=datetime.datetime.now().strftime('%Y%m%d'),
        randchar=''.join(random.sample('abcdefghijklmnopqrstuvwxyz', 8))
    )

class OutwareAccount(BaseWareModel):

    nick  = models.CharField(max_length=16, blank=True, verbose_name=u'APP昵称')

    app_id     = models.CharField(max_length=64, unique=True, default=gen_default_appid, verbose_name=u"回调APPID")
    app_secret = models.CharField(max_length=64, blank=True, verbose_name=u"回调SECRET")

    sign_method = models.CharField(max_length=16, blank=True, default='md5', verbose_name=u'签名方法')
    extras = JSONCharMyField(max_length=512, default={}, verbose_name=u'附加信息')

    class Meta:
        db_table = 'outware_account'
        app_label = 'outware'
        verbose_name = u'外仓/对接APP'
        verbose_name_plural = u'外仓/对接APP'

    def __unicode__(self):
        return '<%s, %s>' % (self.id, self.nick)

    def sign_verify(self, dict_params, sign):
        key_pairs = '&'.join(sorted(['%s=%s'%(k, v) for k, v in dict_params.iteritems()]))
        if self.sign_method == 'md5':
            ow_sign = hashlib.md5(key_pairs + self.app_secret).hexdigest()
            logger.info('小鹿sign:%s'%ow_sign)
            return ow_sign == sign

        return False

    @classmethod
    def get_fengchao_account(cls):
        return cls.objects.first()
