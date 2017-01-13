# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
from django.db import models
from django.db import transaction, IntegrityError
from core.models import BaseModel
from core.fields import JSONCharMyField
from signals import signal_charge_success, create_signal_message

class ChargeOrder(BaseModel):

    CNY = 'cny'
    CURRENCY_CHOICES = (
        (CNY, u'人民币'),
    )

    WX = 'wx'
    WEAPP = 'weapp'
    ALIPAY = 'alipay'
    WX_PUB = 'wx_pub'
    ALIPAY_WAP = 'alipay_wap'
    UPMP_WAP = 'upmp_wap'

    CHANNEL_CHOICES = (
        (WX, u'微信支付'),
        (WEAPP, u'小程序支付'),
        (ALIPAY, u'支付宝支付'),
        (WX_PUB, u'公众号支付'),
        (ALIPAY_WAP, u'支付宝网页支付'),
        (UPMP_WAP, u'银联支付'),
    )

    order_no = models.CharField(max_length=64, unique=True, verbose_name=u'商家订单号')
    channel  = models.CharField(max_length=16, choices=CHANNEL_CHOICES, verbose_name=u'支付渠道')

    livemode = models.BooleanField(default=True, verbose_name=u'正式订单')
    paid     = models.BooleanField(default=False, verbose_name=u'已支付')
    refunded = models.BooleanField(default=False, verbose_name=u'已退款')

    client_ip = models.CharField(max_length=24, verbose_name=u'客户端IP')
    amount   = models.IntegerField(default=0, verbose_name=u'订单金额(分)')
    currency = models.CharField(max_length=16, default=CNY, choices=CURRENCY_CHOICES, verbose_name=u'币种')
    subject  = models.CharField(max_length=64, blank=True, verbose_name=u'标题')
    body     = models.CharField(max_length=256, blank=True, verbose_name=u'详情')

    time_paid = models.DateTimeField(db_index=True, blank=True, null=True, verbose_name=u'付款时间')
    time_expire = models.DateTimeField(db_index=True, blank=True, null=True, verbose_name=u'截止付款时间')
    transaction_no = models.CharField(max_length=64, blank=True, verbose_name=u'支付渠道流水单号')

    amount_refunded = models.IntegerField(default=0, verbose_name=u'退款金额(分)')
    failure_code = models.CharField(max_length=64, blank=True, verbose_name=u'错误编码')
    failure_msg  = models.CharField(max_length=512, blank=True, verbose_name=u'错误描述')
    description = models.CharField(max_length=256, blank=True, verbose_name=u'备注')

    extra   = JSONCharMyField(max_length=512, default={}, verbose_name=u'附加参数')

    class Meta:
        db_table = 'xiaolupay_charge'
        app_label = 'xiaolupay'
        verbose_name = u'小鹿支付/支付记录'
        verbose_name_plural = u'小鹿支付/支付记录列表'

    def is_payable(self):
        if not self.paid and self.time_expire < datetime.datetime.now():
            return True
        return False

    @property
    def credential(self):
        credent = Credential.objects.filter(
                order_no=self.order_no,
                channel=self.channel
            ).first()
        return credent and credent.extra or {}

    def get_or_create_credential(self):
        Credential.objects.get_or_create(
            order_no=self.order_no,
            channel=self.channel
        )
        with transaction.atomic():
            credent = Credential.objects.select_for_update().get(
                order_no=self.order_no,
                channel=self.channel
            )
            if not credent.extra:
                try:
                    from ..services.charge import create_credential
                    credential = create_credential(
                        order_no=self.order_no,
                        amount=self.amount,
                        channel=self.channel,
                        currency=self.currency,
                        subject=self.subject,
                        body=self.body,
                        extra=self.extra,
                        client_ip=self.client_ip,
                    )
                except Exception, exc:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(str(exc), exc_info=True)

                    self.failure_code = 'credential_create_error'
                    self.failure_msg  = str(exc)
                    self.save(update_fields=['failure_code', 'failure_msg'])
                    return {}, False
                credent.extra = credential
                credent.save()
                return credent.extra, True
            return credent.extra, False

    def confirm_paid(self, time_paid, **kwargs):
        update_fields = ['paid', 'time_paid']
        for k, v in kwargs.iteritems():
            if hasattr(self, k) and v:
                setattr(self, k, v)
                update_fields.append(k)

        self.paid = True
        self.time_paid = time_paid
        self.save(update_fields=update_fields)

        signal_message = create_signal_message(
            'xiaolupay.charge_success',
            {
                'id': self.id,
                'object': 'charge',
                'order_no': self.order_no,
                'time_paid': self.time_paid,
                'amount': self.amount,
                'paid': True,
            }
        )
        transaction.on_commit(lambda : signal_charge_success.send_robust(
            sender=signal_message['type'],
            message=signal_message
        ))


    def confirm_refund(self, refund_amount, **kwargs):
        self.refunded = True
        self.amount_refunded = refund_amount
        self.save(update_fields=['refunded', 'amount_refunded'])

    def failure_paid(self, fail_code, fail_msg, **kwargs):
        update_fields = ['paid', 'time_paid']
        for k, v in kwargs.iteritems():
            if hasattr(self, k):
                setattr(self, k, v)
                update_fields.append(k)

        self.failure_code = fail_code
        self.failure_msg = fail_msg
        self.save(update_fields=update_fields)



class Credential(BaseModel):

    order_no = models.CharField(max_length=64, blank=False,  verbose_name=u'商家订单号')
    channel  = models.CharField(max_length=16, choices=ChargeOrder.CHANNEL_CHOICES, blank=False, verbose_name=u'支付渠道')
    extra    = JSONCharMyField(max_length=1024,  default={}, verbose_name=u'渠道凭证')

    class Meta:
        db_table = 'xiaolupay_credential'
        unique_together = ["order_no", "channel"]
        app_label = 'xiaolupay'
        verbose_name = u'小鹿支付/凭证'
        verbose_name_plural = u'小鹿支付/凭证列表'