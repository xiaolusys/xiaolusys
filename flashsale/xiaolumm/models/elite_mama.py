# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime

from django.db import models
from core.models import BaseModel

import logging
logger = logging.getLogger(__name__)

class EliteMamaStatus(BaseModel):
    """ 精英妈妈状态 """
    NORMAL  = 0
    STAGING = 1
    FOLLOUP = 2
    STATUS_CHOICES = (
        (NORMAL, u'正常'),
        (STAGING, u'待跟进'),
        (FOLLOUP, u'跟进中'),
    )

    mama_id = models.IntegerField(unique=True, verbose_name=u'妈妈ID')

    sub_mamacount   = models.IntegerField(default=0, db_index=True, verbose_name=u'下级数量')
    purchase_amount = models.IntegerField(default=0, db_index=True, verbose_name=u'进货金额')
    transfer_amount = models.IntegerField(default=0, db_index=True, verbose_name=u'转给下属')
    return_amount   = models.IntegerField(default=0, db_index=True, verbose_name=u'下属退还')
    sale_amount     = models.IntegerField(default=0, db_index=True, verbose_name=u'买货金额')
    exchg_amount    = models.IntegerField(default=0, db_index=True, verbose_name=u'兑券金额')
    refund_amount   = models.IntegerField(default=0, db_index=True, verbose_name=u'退券金额')

    saleout_rate   = models.FloatField(default=0, db_index=True, verbose_name=u'出货率')
    transfer_rate  = models.FloatField(default=0, db_index=True, verbose_name=u'流通率', help_text='券转移给下属比例')
    refund_rate    = models.FloatField(default=0, db_index=True, verbose_name=u'退券率')

    joined_date = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'加入时间')
    last_active_time = models.DateTimeField(default=datetime.datetime.now, db_index=True, verbose_name=u'最近活跃时间')

    status = models.IntegerField(choices=STATUS_CHOICES, db_index=True, default=NORMAL, verbose_name=u'状态')
    memo   = models.TextField(max_length=1024, verbose_name=u'备注')

    class Meta:
        db_table = 'xiaolumm_elitestatus'
        app_label = 'xiaolumm'
        verbose_name = u'精英妈妈/活跃状态'
        verbose_name_plural = u'精英妈妈/活跃状态列表'

    def save(self, update_fields=[], *args, **kwargs):
        if self.purchase_amount > 0:
            self.saleout_rate = (self.sale_amount + self.exchg_amount) / self.purchase_amount
            self.transfer_rate = min(self.transfer_amount - self.return_amount, 0) / self.purchase_amount
            self.refund_rate   = self.refund_rate / self.purchase_amount
            update_fields.extend(['transfer_rate', 'refund_rate'])
        return super(EliteMamaStatus, self).save(*args, **kwargs)


    def __unicode__(self):
        return u'<%s,%s>' % (self.mama_id, self.status)
