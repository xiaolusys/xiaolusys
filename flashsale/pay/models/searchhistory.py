# coding=utf-8
from __future__ import unicode_literals, absolute_import
import logging
from core.models import BaseModel

from django.db import models

logger = logging.getLogger(__name__)


class UserSearchHistory(BaseModel):
    MODEL_PRODUCT = 'ModelProduct'
    TARGET_CHOICE = (
        (MODEL_PRODUCT, '特卖款式'),
    )

    CLEAR_BY_USER = 'uclear'
    NORMAL = 'normal'
    STATUS_CHOICE = (
        (NORMAL, '正常'),
        (CLEAR_BY_USER, '被用户清除'),
    )

    user_id = models.BigIntegerField(default=0, db_index=True, verbose_name='用户id', help_text='DjangoUserId')
    content = models.CharField(max_length=256, verbose_name=u'搜索内容')
    target = models.CharField(max_length=16, choices=TARGET_CHOICE, db_index=True, verbose_name=u'搜索目标')
    result_count = models.IntegerField(default=0, verbose_name=u'结果条数')
    status = models.CharField(max_length=8, default=NORMAL, choices=STATUS_CHOICE, db_index=True, verbose_name=u'状态')

    class Meta:
        db_table = 'flashsale_user_search_history'
        app_label = 'pay'
        verbose_name = u'特卖商城/用户搜索表'
        verbose_name_plural = u'特卖商城/用户搜索列表'

    def __unicode__(self):
        return '<%s-%s>' % (self.user_id, self.content)
