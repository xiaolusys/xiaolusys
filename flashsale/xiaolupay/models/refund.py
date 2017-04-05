# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import models
from core.models import BaseModel
from signals import signal_refund_success, create_signal_message

"""
{
  "id": "re_y1u944PmfnrTHyvnL0nD0iD1",
  "object": "refund",
  "order_no": "y1u944PmfnrTHyvnL0nD0iD1",
  "amount": 9,
  "created": 1409634160,
  "succeed": true,
  "status": "succeeded",
  "time_succeed": 1409634192,
  "description": "Refund Description",
  "failure_code": null,
  "failure_msg": null,
  "metadata": {},
  "charge": "ch_L8qn10mLmr1GS8e5OODmHaL4",
  "charge_order_no": "123456789",
  "transaction_no": "2004450349201512090096425284"
}
"""

class RefundOrder(BaseModel):

    PENDING = 'pending'
    SUCCESSED = 'succeeded'
    FAILED = 'failed'

    STATUS_CHOICES = (
        (PENDING, u'处理中'),
        (SUCCESSED, u'成功'),
        (FAILED, u'失败'),
    )

    UNSETTLED_FUNDS = 'unsettled_funds'
    RECHARGE_FUNDS  = 'recharge_funds'
    FUNDING_CHOICES = (
        (UNSETTLED_FUNDS, u'使用未结算资金退款'),
        (RECHARGE_FUNDS, u'使用可用余额退款'),
    )

    refund_no = models.CharField(max_length=64, unique=True, blank=False,  verbose_name=u'商家退款编号')
    amount   = models.IntegerField(default=0, verbose_name=u'退款金额(分)')
    succeed  = models.BooleanField(default=False, verbose_name=u'退款成功')
    status   = models.CharField(max_length=16, default=PENDING, choices=STATUS_CHOICES, verbose_name=u'退款状态')
    time_succeed = models.DateTimeField(blank=True, null=True, verbose_name=u'退款成功时间')
    description  = models.CharField(max_length=256, verbose_name=u'退款说明')
    failure_code = models.CharField(max_length=32, blank=True, verbose_name=u'错误码')
    failure_msg  = models.CharField(max_length=128, blank=True, verbose_name=u'错误信息')
    charge = models.ForeignKey('xiaolupay.ChargeOrder', verbose_name=u'支付记录')
    charge_order_no = models.CharField(max_length=32, db_index=True, verbose_name=u'商家支付编号')
    transaction_no  = models.CharField(max_length=64, blank=True, verbose_name=u'渠道流水号')
    funding_source  = models.CharField(max_length=16, blank=True, default=UNSETTLED_FUNDS,
                                       choices=FUNDING_CHOICES, verbose_name=u'渠道流水号')

    class Meta:
        db_table = 'xiaolupay_refund'
        app_label = 'xiaolupay'
        verbose_name = u'小鹿支付/退款'
        verbose_name_plural = u'小鹿支付/退款列表'

    def confirm_refunded(self, succeed_time, **kwargs):
        update_fields = ['succeed', 'time_succeed']
        for k, v in kwargs.iteritems():
            if hasattr(self, k):
                setattr(self, k, v)
                update_fields.append(k)

        self.time_succeed = succeed_time
        self.succeed = True
        self.save(update_fields=update_fields)

        signal_message = create_signal_message(
            'xiaolupay.refund_success',
            {
                'id': self.id,
                'object': 'refund',
                'refund_no': self.order_no,
                'order_no': self.charge_order_no,
                'refund_amount': self.amount,
                'amount': self.amount,
                'time_succeed': self.time_succeed,
                'succeed': True,
                'description': self.description,
            }
        )
        signal_refund_success.send_robust(
            sender=signal_message['type'],
            message=signal_message
        )