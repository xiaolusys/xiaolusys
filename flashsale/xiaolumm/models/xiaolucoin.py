# encoding=utf8
from __future__ import unicode_literals

import datetime
from django.db.models import F
from django.db import models, transaction

from core.models import BaseModel


class XiaoluCoin(BaseModel):
    """
    小鹿币

    4个接口

    1. 创建小鹿币钱包 XiaoluCoin.create()
    2. 充值 recharge()
    3. 消费 consume()
    4. 退款 refund()
    """

    mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u"妈妈编号")
    amount = models.IntegerField(default=0, verbose_name=u"金额(分)")

    class Meta:
        db_table = 'flashsale_xlmm_xiaolucoin'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿币'
        verbose_name_plural = u'小鹿币'

    @classmethod
    def get_or_create(cls, mama_id):
        coin = XiaoluCoin.objects.filter(mama_id=mama_id).first()
        if not coin:
            coin = XiaoluCoin(mama_id=mama_id, amount=0)
            coin.save()
        return coin

    def recharge(self, amount, referal_id=''):
        """
        充值

        referal_id: 充值订单ID
        """
        with transaction.atomic():
            self.amount = F('amount') + amount
            self.save()

            XiaoluCoinLog.create(self.mama_id, XiaoluCoinLog.IN, amount, XiaoluCoinLog.RECHARGE, referal_id=referal_id)

    def consume(self, amount, referal_id=''):
        """
        消费

        referal_id: 消费订单ID
        """
        with transaction.atomic():
            self.amount = F('amount') - amount
            self.save()

            XiaoluCoinLog.create(self.mama_id, XiaoluCoinLog.OUT, amount, XiaoluCoinLog.CONSUME, referal_id=referal_id)

    def refund(self, amount, referal_id=''):
        """
        退款

        referal_id: 退款单ID
        """
        with transaction.atomic():
            self.amount = F('amount') + amount
            self.save()

            XiaoluCoinLog.create(self.mama_id, XiaoluCoinLog.IN, amount, XiaoluCoinLog.REFUND, referal_id=referal_id)


class XiaoluCoinLog(BaseModel):
    """
    禁止直接创建修改此对象, 请调用 XiaoluCoin
    """

    IN  = 'in'
    OUT = 'out'

    IRO_CHOICES = (
        (IN, '收入'),
        (OUT, '支出')
    )

    RECHARGE = 'recharge'
    CONSUME = 'consume'
    REFUND = 'refund'

    SUBJECT_CHOICES = (
        (RECHARGE, '充值'),
        (CONSUME, '消费'),
        (REFUND, '退款')
    )

    mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u"妈妈编号")
    iro_type = models.CharField(max_length=4, choices=IRO_CHOICES, verbose_name=u'收支类型')
    amount = models.IntegerField(default=0, verbose_name=u"金额(分)")
    subject = models.CharField(max_length=16, choices=SUBJECT_CHOICES, db_index=True,
                               null=False, verbose_name=u"记录类型")
    date_field = models.DateField(default=datetime.date.today, verbose_name=u'业务日期')
    referal_id = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'引用id')
    uni_key = models.CharField(max_length=128, unique=True, null=True, verbose_name=u'唯一ID')


    class Meta:
        db_table = 'flashsale_xlmm_xiaolucoinlog'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿币收支记录'
        verbose_name_plural = u'小鹿币收支记录'


    @classmethod
    def gen_uni_key(cls, mama_id, subject, referal_id):
        today = datetime.date.today()
        return '{mama_id}-{subject}-{referal_id}|{today}'.format(
            mama_id=mama_id, today=today, subject=subject, referal_id=referal_id)

    @classmethod
    def create(cls, mama_id, iro_type, amount, subject, referal_id='', uni_key=''):
        uni_key = uni_key or XiaoluCoinLog.gen_uni_key(mama_id, subject, referal_id)

        log = XiaoluCoinLog(mama_id=mama_id, iro_type=iro_type, amount=amount, subject=subject,
                            referal_id=referal_id, uni_key=uni_key)
        log.save()

