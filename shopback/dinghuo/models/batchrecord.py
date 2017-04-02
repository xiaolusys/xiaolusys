# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
import operator
from django.db import models
from django.db.models import Q

from core.models import BaseModel

import logging
logger = logging.getLogger(__name__)


class StockBatchFlowRecord(BaseModel):

    SALEORDER  = 'sorder'
    SALEREFUND = 'srefund'
    RECORD_TYPE_CHOICES = (
        (SALEORDER,  u'特卖订单'),
        (SALEREFUND, u'退货订单'),
    )

    model_id = models.IntegerField(db_index=True, verbose_name=u'款式ID')
    sku_id   = models.IntegerField(db_index=True, verbose_name=u'规格ID')
    record_num  = models.IntegerField(default=0, verbose_name=u'记录数量')

    record_type = models.CharField(max_length=8, choices=RECORD_TYPE_CHOICES, db_index=True, verbose_name=u'记录类型')
    batch_no = models.CharField(max_length=16, db_index=True, verbose_name=u'批次编号')

    referal_id = models.CharField(max_length=32, db_index=True, verbose_name=u'关联ID')
    uni_key  = models.CharField(max_length=32, unique=True, verbose_name=u'唯一键')
    status = models.BooleanField(default=False, db_index=True, verbose_name=u'是否有效')

    finish_time = models.DateTimeField(db_index=True, null=True, blank=True, verbose_name=u'完成时间')

    class Meta:
        db_table = 'flashsale_dinghuo_stockflow'
        app_label = 'dinghuo'
        verbose_name = u'库存|批次流动记录'
        verbose_name_plural = u'库存|批次流动记录列表'

    def as_finished(self):
        self.status = True
        self.finish_time = datetime.datetime.now()
