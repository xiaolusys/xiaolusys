# coding=utf-8
from __future__ import unicode_literals, absolute_import
from core.models import BaseModel
from django.db import models
from .transfer_coupon import CouponTransferRecord
import logging

logger = logging.getLogger(__name__)


class TransferCouponDetail(BaseModel):
    transfer_id = models.IntegerField(db_index=True, verbose_name='流通记录id')
    transfer_type = models.IntegerField(default=0, db_index=True, choices=CouponTransferRecord.TRANSFER_TYPES,
                                        verbose_name=u'流通类型')
    coupon_id = models.BigIntegerField(db_index=True, verbose_name='优惠券id')

    class Meta:
        unique_together = ('transfer_id', 'coupon_id')
        db_table = "flashsale_transfer_detail"
        app_label = 'coupon'
        verbose_name = u"特卖/优惠券/流通明细表"
        verbose_name_plural = u"特卖/优惠券/流通明细列表"

    def __unicode__(self):
        # type: () -> text_type
        return '%s-%s' % (self.transfer_id, self.coupon_id)
