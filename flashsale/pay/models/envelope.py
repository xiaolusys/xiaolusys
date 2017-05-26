# 　coding:utf-8
from __future__ import unicode_literals

import datetime
import logging
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from .base import PayBaseModel

from flashsale.xiaolupay import apis as xiaolupay
from flashsale.xiaolupay.apis.v1 import envelope, transfers
from flashsale.xiaolupay.models.weixin_red_envelope import WeixinRedEnvelope
from core.fields import JSONCharMyField


logger = logging.getLogger(__name__)


class Envelop(PayBaseModel):
    WXPUB = 'wx_pub'
    WX_TRANSFER = 'transfer'
    SANDPAY     = 'sandpay'
    ENVELOP_CHOICES = (
        (WXPUB, u'微信公众红包'),
        (WX_TRANSFER, u'微信企业转账'),
        (SANDPAY, u'银行卡转账'),
    )

    WAIT_SEND = 'wait'
    CONFIRM_SEND = 'confirm'
    CANCEL = 'cancel'
    FAIL = 'fail'

    STATUS_CHOICES = ((WAIT_SEND, u'待发送'),
                      (CONFIRM_SEND, u'已发送'),
                      (FAIL, u'发送失败'),
                      (CANCEL, u'已取消'),)

    CASHOUT = 'cashout'
    ORDER_RED_PAC = 'ordred'
    XLAPP_CASHOUT = 'xlapp'
    LEVEL_1 = 'level1'
    LEVEL_2 = 'level2'
    SUBJECT_CHOICES = (
        (CASHOUT, u'妈妈余额提现'),
        (ORDER_RED_PAC, u'订单红包'),
        (XLAPP_CASHOUT, u'个人零钱提现'),
        (LEVEL_1, u'一级推荐人'),
        (LEVEL_2, u'二级推荐人')
    )

    UNSEND = 'unsend'
    SENDING = 'sending'
    SENT = 'sent'
    SEND_FAILED = 'failed'
    RECEIVED = 'received'
    REFUND = 'refund'

    SEND_STATUS_CHOICES = (
        (UNSEND, u'待发放'),
        (SENDING, u'发放中'),
        (SENT, u'已发放待领取'),
        (SEND_FAILED, u'发放失败'),
        (RECEIVED, u'已领取'),
        (REFUND, u'已退款'),)

    VALID_SEND_STATUS = (SENDING, SENT, RECEIVED)

    customer_id = models.IntegerField(default=0, db_index=True, verbose_name='接收客户ID',
                                      help_text='之前数据可能为0, 2017.5.18添加')
    envelop_id = models.CharField(max_length=28, blank=True, db_index=True, verbose_name=u'红包ID')

    amount = models.IntegerField(default=0, verbose_name=u'红包金额')

    platform = models.CharField(max_length=8, db_index=True, choices=ENVELOP_CHOICES, verbose_name=u'红包发放类型')
    livemode = models.BooleanField(default=True, verbose_name=u'是否有效')

    recipient = models.CharField(max_length=28, db_index=True, verbose_name=u'接收者OPENID/银行卡ID')
    receiver = models.CharField(max_length=64, blank=True, db_index=True, verbose_name=u'用户标识')

    subject = models.CharField(max_length=8, db_index=True, choices=SUBJECT_CHOICES, verbose_name=u'红包主题')
    body = models.CharField(max_length=128, blank=True, verbose_name=u'红包祝福语')
    description = models.CharField(max_length=255, blank=True, verbose_name=u'备注信息')

    status = models.CharField(max_length=8, db_index=True, default=WAIT_SEND,
                              choices=STATUS_CHOICES, verbose_name=u'状态')

    fail_msg    = models.CharField(max_length=64, blank=True, verbose_name='错误提示')
    send_status = models.CharField(max_length=8, db_index=True, default=UNSEND,
                                   choices=SEND_STATUS_CHOICES, verbose_name=u'渠道发送状态')

    referal_id = models.CharField(max_length=32, blank=True, db_index=True, verbose_name=u'引用ID')
    send_time = models.DateTimeField(db_index=True, blank=True, null=True, verbose_name=u'发送时间')
    success_time = models.DateTimeField(blank=True, null=True, verbose_name='成功时间')

    class Meta:
        db_table = 'flashsale_envelop'
        app_label = 'xiaolumm'
        verbose_name = u'微信/红包'
        verbose_name_plural = u'微信/红包列表'

    def __unicode__(self):
        return '%s' % (self.id)

    @property
    def bank_card(self):
        if not hasattr(self, '_bank_account_'):
            if self.platform == self.SANDPAY:
                self._bank_account_ = BankAccount.objects.filter(id=self.recipient).first()
            else:
                self._bank_account_ = None
        return self._bank_account_


    @property
    def amount_cash(self):
        return self.amount / 100.0

    def get_amount_display(self):
        return self.amount_cash

    get_amount_display.allow_tags = True
    get_amount_display.admin_order_field = 'amount'
    get_amount_display.short_description = u"红包金额"

    def handle_envelop_by_pingpp(self, envelopd):
        """
        envelopd为pingpp的返回结果
        用于新微信红包接口替换ping++接口时处理旧的ping++红包时使用
        """
        from flashsale.pay.models import BudgetLog
        from flashsale.xiaolumm.models import CashOut

        now = datetime.datetime.now()
        status = envelopd['status']
        self.envelop_id = envelopd['id']
        self.livemode = envelopd['livemode']
        self.send_status = status

        delta_hours = self.send_time and ((now - self.send_time).total_seconds() / (60*60)) or 0
        # 超过72小时，一直是发送中，则退回用户账户。
        # ping++接口bug，微信拦截风险账号的红包，状态一直是发放中，不会改变，红包默认24小时不领取会退回
        if status == self.SENDING and delta_hours > 72:
            self.status = Envelop.FAIL
            self.refund_envelop()
            self.save()
            return

        if status in (self.SENDING, self.SENT, self.RECEIVED):
            self.send_time = self.send_time or now
            self.status = Envelop.CONFIRM_SEND

            if self.subject == Envelop.XLAPP_CASHOUT:
                blog = BudgetLog.objects.filter(id=self.referal_id)
                blog.confirm_budget_log()
            elif self.subject == Envelop.CASHOUT:
                cashout = CashOut.objects.filter(id=self.referal_id).first()
                cashout.approve_cashout() if cashout else None

        elif status in (self.SEND_FAILED, self.REFUND):
            self.status = Envelop.FAIL
            self.refund_envelop()
            logger.info({
                'action': 'envelop',
                'status': self.status,
                'enveop_id': self.envelop_id,
                'mama_id': self.receiver
            })
        self.save()

    def handle_envelop(self, envelopd):
        """
        envelopd => flashsale.xiaolupay.models.weixin_red_envelope.WeixinRedEnvelope
        """
        from flashsale.pay.models import BudgetLog
        from flashsale.xiaolumm.models import CashOut

        now = datetime.datetime.now()
        status = envelopd.status
        self.envelop_id = envelopd.mch_billno
        self.send_status = status.lower()

        if status in (WeixinRedEnvelope.SENDING, WeixinRedEnvelope.SENT, WeixinRedEnvelope.RECEIVED):
            self.send_time = self.send_time or now
            self.status = Envelop.CONFIRM_SEND

            if self.subject == Envelop.XLAPP_CASHOUT:
                bg = BudgetLog.objects.filter(id=self.referal_id).first()
                bg.confirm_budget_log() if bg else None

            if self.subject == Envelop.CASHOUT:
                cashout = CashOut.objects.filter(id=self.referal_id).first()
                cashout.approve_cashout() if cashout else None

        elif status in (WeixinRedEnvelope.FAILED, WeixinRedEnvelope.REFUND):
            self.status = Envelop.FAIL
            self.refund_envelop()
            logger.info({
                'action': 'envelop',
                'status': self.status,
                'enveop_id': self.envelop_id,
                'mama_id': self.receiver
            })
        self.save()

    def send_envelop_by_pingpp(self):
        if self.envelop_id:
            redenvelope = xiaolupay.RedEnvelope.retrieve(self.envelop_id)
            self.handle_envelop_by_pingpp(redenvelope)
        else:
            try:
                redenvelope = xiaolupay.RedEnvelope.create(
                    order_no=str(self.id),
                    channel=self.platform,
                    amount=self.amount,
                    subject=self.get_subject_display(),
                    body=self.body,
                    currency='cny',
                    app=dict(id=settings.PINGPP_APPID),
                    extra=dict(nick_name=u'上海己美网络科技', send_name=u'小鹿美美'),
                    recipient=self.recipient,
                    description=self.description
                )
            except Exception, exc:
                self.status = Envelop.FAIL
                self.save()
                self.refund_envelop()
                raise exc
            else:
                self.handle_envelop_by_pingpp(redenvelope)

    def handle_sandpay_transfer_result(self, transfer):
        from flashsale.pay.models import BudgetLog
        if self.send_status in (Envelop.RECEIVED, Envelop.FAIL):
            return

        self.send_time = self.send_time or datetime.datetime.now()
        self.envelop_id = transfer.order_code

        if transfer.success:
            self.status = Envelop.CONFIRM_SEND
            self.send_status = Envelop.RECEIVED
            self.save()
            bg = BudgetLog.objects.filter(id=self.referal_id).first()
            if bg:
                bg.confirm_budget_log()
        elif transfer.fail:
            self.status = Envelop.FAIL
            self.send_status = Envelop.SEND_FAILED
            self.save()
            self.refund_envelop()
        else:
            # 处理中 pending
            self.status = Envelop.CONFIRM_SEND
            self.send_status = Envelop.SENDING
            self.save()

    def send_envelop(self):
        from flashsale.pay.models import BudgetLog

        if self.envelop_id or self.status != Envelop.WAIT_SEND:
            raise Exception(u'不能重复发送')

        envelope_unikey = 'xlmm%s' % (self.id)
        if self.platform == Envelop.WX_TRANSFER:
            flow_amount = self.amount
            name = self.body
            desc = u'小鹿美美提现'
            trade_id = envelope_unikey

            try:
                success = transfers.transfer(self.recipient, name, flow_amount, desc, trade_id)
                if success:
                    self.status = Envelop.CONFIRM_SEND
                    self.send_status = Envelop.RECEIVED
                    self.send_time = datetime.datetime.now()
                    self.envelop_id = trade_id
                    self.save()
                    bg = BudgetLog.objects.filter(id=self.referal_id).first()
                    if bg:
                        bg.confirm_budget_log()
                else:
                    self.status = Envelop.FAIL
                    self.send_status = Envelop.SEND_FAILED
                    self.send_time = datetime.datetime.now()
                    self.envelop_id = trade_id
                    self.save()
                    self.refund_envelop()
            except Exception, exc:
                logger.error('转账错误%s' % exc, exc_info=True)
                self.status = Envelop.FAIL
                self.fail_msg = str(exc)
                self.save()

        elif self.platform == Envelop.SANDPAY:
            # TODO 红包异步发送回调结果,　需主动查询, 目前通过取消红包时去检查转账状态
            try:
                band_card = BankAccount.objects.get(id=self.recipient)
                transfer  = transfers.Transfer.create(
                    envelope_unikey,
                    'sandpay',
                    self.amount,
                    u'你的铺子提现',
                    mch_id=settings.SANDPAY_MERCHANT_ID,
                    extras={
                        'accNo': band_card.account_no,
                        'accName': band_card.account_name,
                        'payMode': 1,
                        'channelType': '07'
                    },
                )
                self.handle_sandpay_transfer_result(transfer)
            except Exception, exc:
                logger.error('转账错误%s' % exc, exc_info=True)
                self.status = Envelop.FAIL
                self.fail_msg = str(exc)
                self.save()
        else:
            try:
                redenvelope = envelope.create(
                    order_no=envelope_unikey,
                    amount=self.amount,
                    subject=self.get_subject_display(),
                    body=self.body,
                    recipient=self.recipient,
                    remark=self.description
                )
                self.status = Envelop.CONFIRM_SEND
                self.save()
            except Exception, exc:
                self.fail_msg = str(exc)
                self.status = Envelop.FAIL
                self.save()
                self.refund_envelop()
                raise exc
            else:
                self.handle_envelop(redenvelope)

    def refund_envelop(self):
        from flashsale.pay.models import BudgetLog
        from flashsale.xiaolumm.models import CashOut

        # 小鹿钱包提现
        if self.subject == self.XLAPP_CASHOUT:
            bg = BudgetLog.objects.get(id=self.referal_id, budget_log_type=BudgetLog.BG_CASHOUT)
            bg.confirm_budget_log()
            BudgetLog.create(bg.customer_id, BudgetLog.BUDGET_IN, bg.flow_amount, BudgetLog.BG_CASHOUT_FAIL)

        # 妈妈钱包提现
        if self.subject == self.CASHOUT:
            cashout = CashOut.objects.filter(id=self.referal_id).first()
            if not cashout:
                return
            if cashout.status == CashOut.PENDING:
                cashout.cancel_cashout()
            else:
                cashout.fail_and_return()

    def is_weixin_send_fail(self):
        return self.send_status in (Envelop.FAIL, Envelop.SEND_FAILED)

    def cancel_envelop(self):
        # 取消红包，同时退款
        # 如果银行卡转账，需要去查询当前渠道的转账记录状态
        if self.envelop_id and self.platform == Envelop.SANDPAY:
            from flashsale.pay.models import BudgetLog
            transfer = transfers.Transfer.retrieve(self.envelop_id)
            self.handle_sandpay_transfer_result(transfer)

        # TODO@需要调用微信红包接口, 如果微信红包状态为失败，给予退款
        if not self.envelop_id or self.is_weixin_send_fail():  # 只有待发放状态可以取消红包
            self.status = Envelop.CANCEL
            self.save(update_fields=['status'])
            self.refund_envelop()
            return True
        return False


def push_envelop_get_msg(sender, instance, created, **kwargs):
    """ 发送红包待领取状态的时候　给妈妈及时领取推送消息　"""
    from flashsale.xiaolumm.tasks import task_push_mama_cashout_msg
    sent_status = instance.send_status
    if sent_status != Envelop.SENT:
        return
    task_push_mama_cashout_msg.delay(instance)


post_save.connect(push_envelop_get_msg, sender=Envelop)

class BankAccount(models.Model):
    """ 是否考虑可被供应商使用? """
    NORMAL = 0
    DELETE = 1
    STATUS_CHOICES = (
        (NORMAL, u'正常'),
        (DELETE, u'作废'),
    )

    user = models.ForeignKey('auth.user', verbose_name='所属用户')
    account_no   = models.CharField(max_length=32, verbose_name='银行卡账号')
    account_name = models.CharField(max_length=32, verbose_name='银行卡持有人名称')
    bank_name    = models.CharField(max_length=32, verbose_name='银行全称')

    created  = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='创建时间')
    modified = models.DateTimeField(auto_now=True, verbose_name='创建时间')

    default = models.BooleanField(default=False, verbose_name='默认使用')
    status  = models.SmallIntegerField(default=NORMAL, choices=STATUS_CHOICES, db_index=True, verbose_name='状态')

    # uni_key = models.CharField(max_length=96, unique=True, verbose_name='唯一键')
    extras  = JSONCharMyField(max_length=512, default={}, verbose_name='附加信息')

    class Meta:
        db_table = 'flashsale_bankaccount'
        app_label = 'pay'
        verbose_name = u'用户/银行卡'
        verbose_name_plural = u'用户/银行卡'

    @classmethod
    def gen_uni_key(cls, account_no, account_name, user_id):
        return '{}-{}-{}'.format(account_no, account_name, user_id)

    def set_invalid(self):
        self.status = self.DELETE
        self.save()

        if self.default:
            first_card = BankAccount.objects.filter(user=self.user, status=self.NORMAL).first()
            if first_card:
                first_card.set_default()


    def set_default(self):
        self.default = True
        self.save()

        user_banks = BankAccount.objects.filter(user=self.user , status=self.NORMAL).exclude(id=self.id)
        if user_banks.exists():
            user_banks.update(default=False)


