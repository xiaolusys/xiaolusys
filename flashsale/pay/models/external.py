# coding=utf-8
from __future__ import unicode_literals

from django.db import models
from .base import PayBaseModel

class TradeCharge(PayBaseModel):
    order_no = models.CharField(max_length=40, verbose_name=u'订单ID')
    charge = models.CharField(max_length=28, verbose_name=u'支付编号')

    paid = models.BooleanField(db_index=True, default=False, verbose_name=u'付款')
    refunded = models.BooleanField(db_index=True, default=False, verbose_name=u'退款')

    channel = models.CharField(max_length=16, blank=True, verbose_name=u'支付方式')
    amount = models.CharField(max_length=10, blank=True, verbose_name=u'付款金额')
    currency = models.CharField(max_length=8, blank=True, verbose_name=u'币种')

    transaction_no = models.CharField(max_length=28, blank=True, verbose_name=u'事务NO')
    amount_refunded = models.CharField(max_length=16, blank=True, verbose_name=u'退款金额')

    failure_code = models.CharField(max_length=16, blank=True, verbose_name=u'错误编码')
    failure_msg = models.CharField(max_length=16, blank=True, verbose_name=u'错误信息')

    #     out_trade_no    = models.CharField(max_length=32,db_index=True,blank=True,verbose_name=u'外部交易ID')

    time_paid = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'付款时间')
    time_expire = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'失效时间')

    class Meta:
        db_table = 'flashsale_trade_charge'
        unique_together = ("order_no", "charge")
        app_label = 'pay'
        verbose_name = u'特卖支付/交易'
        verbose_name_plural = u'特卖交易/支付列表'

    def __unicode__(self):
        return '<%s>' % (self.id)