# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
import time
from django.db import models, transaction
from core.fields import JSONCharMyField
from .. import conf

class TransferOrder(models.Model):

    PENDING = 0
    SUCCESS = 1
    FAIL    = 2
    RESULT_FLAG_CHOICES = (
        (PENDING, '处理中'),
        (SUCCESS, '成功'),
        (FAIL, '失败'),
    )

    mch_id  = models.CharField(max_length=32, blank=True, verbose_name='渠道商户ID')
    channel = models.CharField(max_length=16, db_index=True, default=conf.WX_PUB,
                               choices=conf.CHANNEL_CHOICES , verbose_name='转账渠道')

    order_code = models.CharField(max_length=32, db_index=True, verbose_name='商户订单号')
    tran_code = models.CharField(max_length=32, db_index=True, blank=True, verbose_name='渠道流水号')


    amount = models.IntegerField(default=0, verbose_name='金额(分)')
    desc = models.CharField(max_length=256, blank=True, verbose_name='企业付款描述信息')

    return_code = models.CharField(max_length=16, verbose_name='返回状态码')
    return_msg = models.CharField(max_length=128, blank=True, verbose_name='返回信息')

    status  = models.IntegerField(db_index=True, choices=RESULT_FLAG_CHOICES, default=PENDING, verbose_name=u'处理状态')

    uni_key = models.CharField(max_length=64, unique=True, verbose_name=u'唯一键')

    order_time = models.DateTimeField(db_index=True, default=datetime.datetime.now, verbose_name=u'业务时间')
    success_time = models.DateTimeField(null=True, verbose_name=u'成功时间')

    time_out = models.IntegerField(default=0, verbose_name=u'超时时间(s)')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    extras = JSONCharMyField(max_length=5012, default={}, verbose_name='附加参数')

    class Meta:
        db_table = 'xiaolupay_transfer_order'
        app_label = 'xiaolupay'
        verbose_name = '小鹿支付/企业统一转账'
        verbose_name_plural = '小鹿支付/企业统一转账'

    @classmethod
    def gen_uni_key(cls, order_code):
        return '{}'.format(order_code)

    @classmethod
    def format_order_code(cls, order_code):
        return '%sii%s' % (datetime.datetime.now().strftime('%Y%m%d'), str(order_code).rjust(2, str('0')))

    @classmethod
    def parse_order_code(cls, format_order_code):
        return format_order_code.split('ii')[1].lstrip('0')

    @property
    def sandpay_data(self):
        from ..libs.sandpay import SandpayConf

        data = self.extras.get(self.channel, {}).copy()
        product_attr = SandpayConf.PRO_TRANS2PRI
        tran_time = self.order_time or datetime.datetime.now()
        data.update({
            'productId': product_attr[0],
            'accAttr': product_attr[1],
            'tranTime': tran_time,
            'timeOut': tran_time + datetime.timedelta(seconds=self.time_out),
            'orderCode': self.order_code,
            'tranAmt': str(self.amount).rjust(12, str('0')),
            'accType': SandpayConf.ACC_TYPE_BANK,
            'currencyCode': SandpayConf.DEFAULT_CURRENCY_CODE,
            'noticeUrl': SandpayConf.SANDPAY_AGENT_PAY_NOTICE_URL
        })
        return data

    def start_transfer(self):
        from ..services.transfer import start_transfer
        return start_transfer(self)

    def is_success(self):
        return self.status == TransferOrder.SUCCESS

    def is_fail(self):
        return self.status == TransferOrder.FAIL

    def confirm_completed(self):
        from signals import signal_card_transfer, create_signal_message

        signal_message = create_signal_message(
            'xiaolupay.transfer_success',
            {
                'id': self.id,
                'object': 'transfer',
                'channel': self.channel,
                'order_code': self.order_code,
                'success_time': self.success_time,
                'amount': self.amount,
            }
        )
        signal_card_transfer.send_robust(
            sender=signal_message['type'],
            message=signal_message
        )

    def confirm_fail(self):
        from signals import signal_card_transfer, create_signal_message

        signal_message = create_signal_message(
            'xiaolupay.transfer_fail',
            {
                'id': self.id,
                'object': 'transfer',
                'channel': self.channel,
                'order_code': self.order_code,
                'success_time': None,
                'amount': self.amount,
            }
        )
        signal_card_transfer.send_robust(
            sender=signal_message['type'],
            message=signal_message
        )

    def to_apidict(self):
        order_code = TransferOrder.parse_order_code(self.order_code)
        return {
            'id': self.id,
            'object': 'TransferOrder',
            'channel': self.channel,
            'order_code': order_code,
            'amount': self.amount,
            'desc': self.desc,
            'status': self.status,
            'success': self.is_success(),
            'order_time': self.order_time,
            'extras': self.extras.get(self.channel, {}).copy()
        }

