# -*- coding:utf8 -*-
import datetime
from django.db import models

from .managers import InterceptTradeManager


class InterceptTrade(models.Model):
    COMPLETE = 1
    UNCOMPLETE = 0

    STATUS_CHOICES = ((UNCOMPLETE, u'未拦截'),
                      (COMPLETE, u'已拦截'))

    buyer_nick = models.CharField(max_length=64, db_index=True
                                  , blank=True, verbose_name=u'买家昵称')

    buyer_mobile = models.CharField(max_length=24, db_index=True, blank=True
                                    , verbose_name=u'手机')

    serial_no = models.CharField(max_length=64, db_index=True, blank=True
                                 , verbose_name=u'外部单号')

    trade_id = models.BigIntegerField(null=True, blank=True, verbose_name=u'系统订单ID')

    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改时间')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u'创建日期')

    status = models.IntegerField(default=UNCOMPLETE, choices=STATUS_CHOICES, verbose_name=u'状态')

    objects = InterceptTradeManager()

    class Meta:
        db_table = 'shop_intercept_trade'
        app_label = 'memorule'
        verbose_name = u'拦截订单'
        verbose_name_plural = u'拦截订单列表'

    def __unicode__(self):
        return self.buyer_nick
