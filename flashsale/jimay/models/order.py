# coding: utf8
from __future__ import absolute_import, unicode_literals

import datetime
import hashlib
from django.db import models, transaction
from django.dispatch import receiver
from django.utils.functional import cached_property

from signals.jimay import signal_jimay_agent_order_ensure, signal_jimay_agent_order_paid
from core.utils.unikey import uniqid


def gen_uuid_order_no():
    return uniqid('%s%s' % (JimayAgentOrder.PREFIX_CODE, datetime.date.today().strftime('%y%m%d')))


class JimayAgentOrder(models.Model):

    PREFIX_CODE = 'ad'

    ST_CREATE = 0
    ST_ENSURE = 1
    ST_PAID  = 2
    ST_SEND   = 3
    ST_COMPLETED = 4
    ST_CANCEL = 5

    ST_CHOICES = (
        (ST_CREATE, '已提交申请'),
        (ST_ENSURE, '已确认订金'),
        (ST_PAID, '已确认付款'),
        (ST_SEND, '已打包出库'),
        (ST_COMPLETED, '已签收完成'),
        (ST_CANCEL, '已取消订货'),
    )

    buyer = models.ForeignKey('pay.Customer', verbose_name='原始用户')
    order_no = models.CharField(max_length=24, default=gen_uuid_order_no, unique=True, verbose_name='订单编号')

    title    = models.CharField(max_length=64, blank=True, verbose_name='商品名称')
    pic_path = models.CharField(max_length=256, blank=True, verbose_name='商品图片')
    model_id = models.IntegerField(default=0, verbose_name='款式ID')
    sku_id   = models.IntegerField(default=0, verbose_name='SKUID')
    num      = models.IntegerField(default=0, verbose_name='数量')
    total_fee = models.IntegerField(default=0, verbose_name='商品总价(分)', help_text='精度分')
    payment = models.IntegerField(default=0, verbose_name='支付金额(分)', help_text='精度分,现默认由运营人员填写')

    address = models.ForeignKey('pay.UserAddress', related_name='jimay_agent_manager', verbose_name='用户地址')

    status  = models.IntegerField(default=ST_CREATE, db_index=True, choices=ST_CHOICES, verbose_name='状态')

    ensure_time = models.DateTimeField(blank=True, null=True, verbose_name='审核时间')
    pay_time = models.DateTimeField(blank=True, null=True, verbose_name='付款时间')

    logistic = models.ForeignKey('logistics.LogisticsCompany', null=True, blank=True, verbose_name='物流公司')
    logistic_no = models.CharField(max_length=32, blank=True, verbose_name='物流单号')
    send_time = models.DateTimeField(blank=True, null=True, verbose_name='发货时间')

    manager = models.ForeignKey('auth.user', blank=True, null=True, verbose_name='管理员')

    sys_memo = models.CharField(max_length=512, blank=True, verbose_name='系统备注')
    created  = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name='修改日期')

    class Meta:
        db_table = 'jimay_agentorder'
        app_label = 'jimay'
        verbose_name = '己美医学/订货记录'
        verbose_name_plural = '己美医学/订货记录'

    def __unicode__(self):
        return '%s,%s' % (self.id, self.buyer)

    @classmethod
    def gen_unique_order_no(cls):
        return gen_uuid_order_no()

    @classmethod
    def is_createable(cls, buyer):
        return not cls.objects.filter(buyer=buyer,status=JimayAgentOrder.ST_CREATE).exists()

    def save(self, *args, **kwargs):
        if self.status == JimayAgentOrder.ST_ENSURE and not self.pay_time:
            self.action_ensure(self.ensure_time or datetime.datetime.now())

        resp = super(JimayAgentOrder, self).save(*args, **kwargs)
        return resp

    def is_cancelable(self):
        return self.status == JimayAgentOrder.ST_CREATE

    def set_status_canceled(self):
        self.status = JimayAgentOrder.ST_CANCEL

    def action_ensure(self, time_ensure):
        """ 订单审核通过 """
        transaction.on_commit(lambda: signal_jimay_agent_order_ensure.send_robust(
            sender=JimayAgentOrder,
            obj=self,
            time_ensure=time_ensure
        ))

    def action_paid(self, time_paid):
        """ 订单支付通知 """
        transaction.on_commit(lambda: signal_jimay_agent_order_paid.send_robust(
            sender=JimayAgentOrder,
            obj=self,
            time_paid=time_paid
        ))

@receiver(signal_jimay_agent_order_ensure, sender=JimayAgentOrder)
def jimay_order_ensure_weixin_paynotify(sender, obj, time_ensure, **kwargs):
    try:
        from shopapp.weixin.models import WeiXinAccount
        from ..tasks import task_weixin_asynchronous_send_payqrcode
        from django.conf import settings

        wx_account = WeiXinAccount.objects.get(app_id=settings.WX_JIMAY_APPID)
        task_weixin_asynchronous_send_payqrcode.delay(
            wx_account.account_id, obj.buyer.id,
            'wxpub',
            ('您的订货单已审核通过, 需支付金额:￥%s元, 请长按识别二维码转账, '
                +'转账时请备注: %s_的订货号_%s .(如果需要支付宝付款, 请点击菜单[己美医学]/[支付宝付款码])'
            ) % (obj.payment * 0.01, obj.buyer.mobile, obj.id)
        )
    except Exception, exc:
        print exc
