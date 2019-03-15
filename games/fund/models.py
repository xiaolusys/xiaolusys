# -*- coding:utf-8 -*-.
from __future__ import unicode_literals

from datetime import datetime, date
from django.db import models
from jsonfield import JSONField as JSONCharMyField

from core.utils.timeutils import get_previous_byday

# Create your models here.

NOTIFY_WEEKMSG = """
弘利基金上周收益(单位:美元)
=====================
截止日期：{cur_date}
账户姓名：{buyer_name}
上周收益：{lastweek_profit:.2f}
年化利率：{annual_yield_rate}%
购入本金：{buy_amount:.2f}
新购日期：{last_buy_date}
有效天数：{valid_days}
累计收益：{earned_profit:.2f}
=========说明=========
年化利率: 即购买时约定的年收益率;
购入本金: 累计购入基金金额的总和;
新购日期: 最后一次购买的日期;
有效天数: 从新购日期到截止日期的天数;
累计收益: 到截止日期累计收益金额;
"""

NOTIFY_CLICKMSG = """
弘利基金实时收益(单位:美元)
=====================
截止日期：{cur_date}
账户姓名：{buyer_name}
年化利率：{annual_yield_rate}%
购入本金：{buy_amount:.2f}
新购日期：{last_buy_date}
有效天数：{valid_days}
累计收益：{earned_profit:.2f}
=========说明=========
年化利率: 即购买时约定的年收益率;
购入本金: 累计购入基金金额的总和;
新购日期: 最后一次购买的日期;
有效天数: 从新购日期到截止日期的天数;
累计收益: 到截止日期累计收益金额;
"""


class FundBuyerAccount(models.Model):

    APPLYING = 0
    HOLDING  = 1
    EXITED   = 2

    STATUS_CHOICES = (
        (APPLYING, '申请中'),
        (HOLDING,  '已购入'),
        (EXITED, '已清退'),
    )

    customer_id = models.IntegerField(unique=True, blank=False, null=False, verbose_name='关联用户ID')

    mobile = models.CharField(max_length=11, null=False, blank=False, verbose_name=u'手机号')
    openid     = models.CharField(max_length=32, blank=True, null=True, verbose_name=u'OPENID')
    buyer_name = models.CharField(max_length=16, blank=False, db_index=True, verbose_name=u'姓名')

    buy_amount = models.IntegerField(default=0, verbose_name=u'当前购买金额($分)')
    settled_earned_profit = models.IntegerField(default=0, verbose_name=u'新购前结算收益($分)',
                                        help_text='在用户多次购入时需将前一笔收益结算完才能处理,这里就是用户新购前未赎回累计收益')

    annual_yield_rate   = models.FloatField(default=0, verbose_name=u'基金年收益率(%)')

    total_buy_amount = models.IntegerField(default=0, verbose_name=u'总购买金额($分)')
    total_earned_profit = models.IntegerField(default=0, verbose_name=u'总结算收益($分)',
                                              help_text='所有已结算的收益总和,不含当前未结算的收益')

    total_cashout = models.IntegerField(default=0, verbose_name=u'总赎回金额($分)')

    last_buy_date = models.DateField(blank=False, null=False, default=datetime.today, verbose_name=u'最后购买日期')

    status   = models.IntegerField(choices=STATUS_CHOICES, default=APPLYING, verbose_name='帐号状态')

    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改日期')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u'创建日期')

    class Meta:
        db_table = u'games_fund_buyeraccount'
        app_label = u'fund'
        verbose_name = u'弘利基金买家帐号'
        verbose_name_plural = u'弘利基金买家帐号列表'

    def __unicode__(self):
        return u'%s(%s)' % (self.buyer_name, self.mobile)

    @property
    def is_applying(self):
        return self.status == self.APPLYING

    @property
    def is_exited(self):
        return self.status == self.EXITED

    @property
    def daily_profit_rate(self):
        return self.annual_yield_rate / 365.0

    def get_week_notify_data(self):
        last_weekend = get_previous_byday('Sunday')
        date_delta   = last_weekend - self.last_buy_date
        lastweek_valid_days = min(max(date_delta.days, 0), 7)
        return {
            "cur_date": last_weekend,
            "buyer_name": self.buyer_name,
            "lastweek_profit": lastweek_valid_days * self.daily_profit_rate * 0.01 * self.buy_amount * 0.01,
            "annual_yield_rate": self.annual_yield_rate,
            "buy_amount": self.buy_amount * 0.01,
            "last_buy_date": self.last_buy_date.strftime("%Y-%m-%d"),
            "valid_days": date_delta.days,
            "earned_profit": (date_delta.days * self.daily_profit_rate * 0.01 * self.buy_amount
                                     + self.settled_earned_profit) * 0.01
        }

    def get_live_notify_data(self):
        today_date = date.today()
        date_delta = today_date - self.last_buy_date
        return {
            "cur_date": today_date,
            "buyer_name": self.buyer_name,
            "lastweek_profit": 0,
            "annual_yield_rate": self.annual_yield_rate,
            "buy_amount": self.buy_amount * 0.01,
            "last_buy_date": self.last_buy_date.strftime("%Y-%m-%d"),
            "valid_days": date_delta.days,
            "earned_profit": (date_delta.days * self.daily_profit_rate * 0.01 * self.buy_amount
                              + self.settled_earned_profit) * 0.01
        }



class FundNotifyMsg(models.Model):

    WEEK_SEND = 1
    CLICK_SEND = 2

    fund_buyer = models.ForeignKey(FundBuyerAccount, verbose_name=u"关联基金用户帐号")

    send_data  = JSONCharMyField(max_length=5120, blank=False, default={}, verbose_name=u'发送消息数据')

    is_send   = models.BooleanField(default=False, verbose_name=u'是否发送')
    send_time = models.DateTimeField(db_index=True, blank=True, null=True, verbose_name=u'发送时间')

    send_type = models.IntegerField(db_index=True, default=2,
                                    choices=((WEEK_SEND, '每周定时'),(CLICK_SEND, '手动查询')), verbose_name='发送类型')

    modified = models.DateTimeField(auto_now=True, blank=True, null=True, verbose_name=u'修改日期')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u'创建日期')

    class Meta:
        db_table = u'games_fund_notifymsg'
        app_label = u'fund'
        verbose_name = u'弘利基金消息通知'
        verbose_name_plural = u'弘利基金消息通知列表'

    def __unicode__(self):
        return u'%s(id:%s)' % (self.fund_buyer, self.id)

    def get_notify_message(self):
        if self.send_type == self.WEEK_SEND:
            return NOTIFY_WEEKMSG.format(**self.send_data)

        return NOTIFY_CLICKMSG.format(**self.send_data)

    def confirm_send(self):
        self.is_send = True
        self.send_time = datetime.now()
        self.save()
