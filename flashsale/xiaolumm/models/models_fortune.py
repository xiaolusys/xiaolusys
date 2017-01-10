# coding=utf-8
from __future__ import unicode_literals

from django.db import models, transaction
from django.db.models import Sum, F
from core.models import BaseModel
from django.db.models.signals import post_save, pre_save
from django.conf import settings
import datetime, urlparse
from core.fields import JSONCharMyField
from flashsale.xiaolumm.models.models import XiaoluMama
from flashsale.xiaolumm.signals import clickcarry_signal
import logging

logger = logging.getLogger('django.request')


def get_choice_name(choices, val):
    """
    iterate over choices and find the name for this val
    """
    name = ""
    for entry in choices:
        if entry[0] == val:
            name = entry[1]
    return name


#
# Use from flashsale.xiaolumm.models import CashOut
#
# class CashOut(BaseModel):
#    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'), (3, u'取消'),)
#    mama_id = models.BigIntegerField(default=0, unique=True, verbose_name=u'小鹿妈妈id')
#    amount = models.IntegerField(default=0, verbose_name=u'数额')
#    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态')
#
#    class Meta:
#        db_table = 'flashsale_xlmm_cashout'
#        verbose_name = u'妈妈提现'
#        verbose_name_plural = u'妈妈提现列表'
#
#    def is_confirmed(self):
#        return self.status == 2
#
#    def amount_display(self):
#        return float('%.2f' % (self.amount * 0.01))


# The time to switch to xiaolumama v2.0
MAMA_FORTUNE_HISTORY_LAST_DAY = datetime.date(2016, 03, 24)


def default_mama_extras():
    """ other mama information """
    return {
        "qrcode_url":
            {
                "home_page_qrcode_url": "",
                "app_download_qrcode_url": ""
            }
    }


class MamaFortune(BaseModel):
    MAMA_LEVELS = ((0, u'新手妈妈'), (1, u'金牌妈妈'), (2, u'钻石妈妈'), (3, u'皇冠妈妈'), (4, u'金冠妈妈'))
    mama_id = models.BigIntegerField(default=0, unique=True, verbose_name=u'小鹿妈妈id')
    mama_name = models.CharField(max_length=32, blank=True, verbose_name=u'名称')
    mama_level = models.IntegerField(default=0, choices=MAMA_LEVELS, verbose_name=u'级别')

    fans_num = models.IntegerField(default=0, verbose_name=u'粉丝数')
    invite_num = models.IntegerField(default=0, verbose_name=u'邀请数')
    invite_trial_num = models.IntegerField(default=0, verbose_name=u'试用妈妈邀请数')
    invite_all_num = models.IntegerField(default=0, verbose_name=u'总邀请数')
    active_normal_num = models.IntegerField(default=0, verbose_name=u'普通妈妈激活数')
    active_trial_num = models.IntegerField(default=0, verbose_name=u'试用妈妈激活数')
    active_all_num = models.IntegerField(default=0, verbose_name=u'总激活数')
    hasale_normal_num = models.IntegerField(default=0, verbose_name=u'出货普通妈妈数')
    hasale_trial_num = models.IntegerField(default=0, verbose_name=u'出货试用妈妈数')
    hasale_all_num = models.IntegerField(default=0, verbose_name=u'出货妈妈总数')

    order_num = models.IntegerField(default=0, verbose_name=u'订单数')

    carry_pending = models.IntegerField(default=0, verbose_name=u'待确定收益')
    carry_confirmed = models.IntegerField(default=0, verbose_name=u'已确定收益')
    carry_cashout = models.IntegerField(default=0, verbose_name=u'已提现金额')

    history_pending = models.IntegerField(default=0, verbose_name=u'历史待确定收益')
    history_confirmed = models.IntegerField(default=0, verbose_name=u'历史已确定收益')
    history_cashout = models.IntegerField(default=0, verbose_name=u'历史已提现收益')
    history_last_day = models.DateField(default=MAMA_FORTUNE_HISTORY_LAST_DAY, verbose_name=u'历史结束日期')

    active_value_num = models.IntegerField(default=0, verbose_name=u'活跃值')
    today_visitor_num = models.IntegerField(default=0, verbose_name=u'今日访客数')
    extras = JSONCharMyField(max_length=1024, default=default_mama_extras, blank=True,
                             null=True, verbose_name=u"附加信息")

    class Meta:
        db_table = 'flashsale_xlmm_fortune'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈财富表'
        verbose_name_plural = u'V2/妈妈财富列表'

    def __unicode__(self):
        return '%s,%s' % (self.mama_id, self.mama_name)

    @staticmethod
    def get_by_mamaid(mama_id):
        fortune = MamaFortune.objects.filter(mama_id=mama_id).first()
        if fortune:
            return fortune
        if not XiaoluMama.objects.filter(id=mama_id).first():
            raise Exception(u'提供的小鹿妈妈id不存在：' + str(mama_id))
        fortune = MamaFortune(mama_id=mama_id)
        fortune.save()
        return fortune

    def mama_level_display(self):
        return get_choice_name(self.MAMA_LEVELS, self.mama_level)

    @property
    def cash_total(self):
        return self.carry_pending + self.carry_confirmed + self.history_pending + self.history_confirmed + self.history_cashout

    def cash_total_display(self):
        return float('%.2f' % (self.cash_total * 0.01))

    cash_total_display.short_description = u"总收益"
    cash_total_display.admin_order_field = 'cash_total'

    def carry_num_display(self):
        """ 累计收益数 """
        total = self.carry_pending + self.carry_confirmed + self.history_pending + self.history_confirmed
        return float('%.2f' % (total * 0.01))

    carry_num_display.short_description = u"累计收益"
    carry_num_display.admin_order_field = 'carry_num'

    def cash_num_cents(self):
        """ 余额 """
        total = self.carry_confirmed + self.history_confirmed - self.carry_cashout
        return total

    def cash_num_display(self):
        """ 余额 """
        total = self.carry_confirmed + self.history_confirmed - self.carry_cashout
        return float('%.2f' % (total * 0.01))

    cash_num_display.short_description = u"账户金额"
    cash_num_display.admin_order_field = 'cash_num'

    def carry_pending_display(self):
        total = self.carry_pending + self.history_pending
        return float('%.2f' % (total * 0.01))

    carry_pending_display.short_description = u"待确认收益"

    def carry_confirmed_display(self):
        total = self.carry_confirmed + self.history_confirmed
        return float('%.2f' % (total * 0.01))

    carry_confirmed_display.short_description = u"已确定收益"

    def carry_cashout_display(self):
        return float('%.2f' % (self.carry_cashout * 0.01))

    carry_cashout_display.short_description = u"已提现金额"

    def mama_event_link(self):
        """ 活动页面链接 """
        activity_link = 'pages/featuredEvent.html'

        return settings.M_SITE_URL + settings.M_STATIC_URL + activity_link

    @property
    def home_page_qrcode_url(self):
        return self.extras['qrcode_url']['home_page_qrcode_url']

    @property
    def app_download_qrcode_url(self):
        return self.extras['qrcode_url']['app_download_qrcode_url']

    def get_history_cash_out(self):
        from flashsale.xiaolumm.models import CashOut
        history_last_day= self.history_last_day or MAMA_FORTUNE_HISTORY_LAST_DAY
        return CashOut.objects.filter(xlmm=self.mama_id, status=CashOut.APPROVED, approve_time__lt=history_last_day
                                      ).aggregate(total=Sum('value')).get('total') or 0

    def update_extras_qrcode_url(self, **kwargs):
        """ 更新附加里面的二维码链接信息 """
        extras = self.extras
        change_flag = False
        for k, v in kwargs.items():
            qrcode_url = extras['qrcode_url']
            if qrcode_url.has_key(k) and qrcode_url.get(k) != v:  # 如果当前的和传过来的参数不等则更新
                qrcode_url.update({k: v})
                change_flag = True
        if change_flag:
            self.extras = extras
            self.save()

    @property
    def customer_id(self):
        return self.xlmm and self.xlmm.customer_id or None

    @property
    def xlmm(self):
        if not hasattr(self, '_xiaolumm_xlmm_'):
            from flashsale.xiaolumm.models.models import XiaoluMama
            self._xiaolumm_xlmm_ = XiaoluMama.objects.filter(id=self.mama_id).first()
        return self._xiaolumm_xlmm_

    @property
    def week_mama_carry(self):
        """
        WeekMamaCarryTotal instance
        """
        if not hasattr(self, '_week_mama_carry_'):
            from flashsale.xiaolumm.models import WeekMamaCarryTotal, WeekRank

            self._week_mama_carry_ = WeekMamaCarryTotal.objects.filter(mama_id=self.mama_id,
                                                                       stat_time=WeekRank.this_week_time()).first()
        return self._week_mama_carry_

    @property
    def week_mama_team_carry(self):
        if not hasattr(self, '_week_mama_team_carry_'):
            from flashsale.xiaolumm.models import WeekMamaTeamCarryTotal, WeekRank

            self._week_mama_team_carry_ = WeekMamaTeamCarryTotal.objects.filter(mama_id=self.mama_id,
                                                                                stat_time=WeekRank.this_week_time()).first()
        return self._week_mama_team_carry_


# The task_send_activate_award() should not be triggered here, because MamaFortune gets
# updated several times a day. The task should be triggered only trail_num gets changed.
#
#def send_activate_award(sender, instance, created, **kwargs):
#    from flashsale.xiaolumm import tasks_mama_fortune
#    if instance.invite_trial_num >= 2:
#        tasks_mama_fortune.task_send_activate_award.delay(instance.mama_id)
#
#post_save.connect(send_activate_award,
#                  sender=MamaFortune, dispatch_uid='post_save_send_activate_award')


def update_week_carry_total(sender, instance, created, **kwargs):
    if instance.xlmm and (not instance.xlmm.is_staff) and instance.xlmm.is_available_rank():
        from flashsale.xiaolumm.tasks import task_fortune_update_week_carry_total, task_fortune_update_activity_carry_total
        from flashsale.xiaolumm.models.carry_total import RankActivity
        task_fortune_update_week_carry_total.delay(instance.mama_id)
        activity = RankActivity.now_activity()
        if activity:
            task_fortune_update_activity_carry_total.delay(activity, instance.mama_id)


post_save.connect(update_week_carry_total,
                  sender=MamaFortune, dispatch_uid='post_save_task_fortune_update_week_carry_total')


class DailyStats(BaseModel):
    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'),)
    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    today_visitor_num = models.IntegerField(default=0, verbose_name=u'今日访客数')
    today_order_num = models.IntegerField(default=0, verbose_name=u'今日订单数')
    today_carry_num = models.IntegerField(default=0, verbose_name=u'今日收益数')
    today_active_value = models.IntegerField(default=0, verbose_name=u'今日活跃值')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    status = models.IntegerField(default=1, choices=STATUS_TYPES, verbose_name=u'状态')  # 待确定/已确定

    class Meta:
        db_table = 'flashsale_xlmm_daily_stats'
        app_label = 'xiaolumm'
        verbose_name = u'V2/每日数据'
        verbose_name_plural = u'V2/每日数据列表'

    def today_carry_num_display(self):
        return float('%.2f' % (self.today_carry_num * 0.01))


def confirm_previous_dailystats(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_confirm_previous_dailystats
    if created:
        mama_id = instance.mama_id
        date_field = instance.date_field
        task_confirm_previous_dailystats.delay(mama_id, date_field, 2)


post_save.connect(confirm_previous_dailystats,
                  sender=DailyStats, dispatch_uid='post_save_confirm_previous_dailystats')


class CarryRecord(BaseModel):
    PENDING = 1
    CONFIRMED = 2
    CANCEL = 3

    STATUS_TYPES = ((PENDING, u'预计收益'),
                    (CONFIRMED, u'确定收益'),
                    (CANCEL, u'已取消'),)

    CR_CLICK = 1
    CR_ORDER = 2
    CR_RECOMMEND = 3
    CARRY_TYPES = ((CR_CLICK, u'返现'),
                   (CR_ORDER, u'佣金'),
                   (CR_RECOMMEND, u'奖金'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    carry_num = models.IntegerField(default=0, verbose_name=u'收益数(分)')
    carry_type = models.IntegerField(default=0, choices=CARRY_TYPES, verbose_name=u'收益类型')  # 返/佣/奖
    carry_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态')  # 待确定/已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_carry_record'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈收入记录'
        verbose_name_plural = u'V2/妈妈收入记录列表'

    def __unicode__(self):
        return '%s,%s,%s' % (self.mama_id, self.carry_type, self.carry_num)

    @property
    def mama(self):
        from flashsale.xiaolumm.models import XiaoluMama
        mama = XiaoluMama.objects.filter(id=self.mama_id).first()
        if mama:
            return mama
        return None

    @classmethod
    def create(cls, mama_id, carry_num, carry_type, desc, uni_key=None, status=None):
        """
        创建收益
        """
        if status not in [CarryRecord.PENDING, CarryRecord.CONFIRMED]:
            return

        uni_key = uni_key or ''
        date_field = datetime.date.today()
        status = status or CarryRecord.CONFIRMED

        carry_record = CarryRecord(mama_id=mama_id, carry_num=carry_num, carry_type=carry_type,
            date_field=date_field, carry_description=desc, uni_key=uni_key, status=status)
        carry_record.save()

        fortune, status = MamaFortune.objects.get_or_create(mama_id=mama_id, defaults={
            'carry_pending': 0,
            'carry_confirmed': 0
        })
        if status == CarryRecord.PENDING:
            fortune.carry_pending = F('carry_pending') + carry_num
        if status == CarryRecord.CONFIRMED:
            fortune.carry_confirmed = F('carry_confirmed') + carry_num
        fortune.save()

    def confirm(self):
        """
        确认收益
        """
        if self.status != CarryRecord.PENDING:
            return

        self.status = CarryRecord.CONFIRMED
        self.save()

        fortune = MamaFortune.objects.filter(mama_id=self.mama_id).first()
        fortune.carry_pending = F('carry_pending') - self.carry_num
        fortune.carry_confirmed = F('carry_confirmed') + self.carry_num
        fortune.save()

    def cancel(self):
        """
        取消收益
        """
        fortune = MamaFortune.objects.filter(mama_id=self.mama_id).first()
        if self.status == CarryRecord.PENDING:
            fortune.carry_pending = F('carry_pending') - self.carry_num
        if self.status == CarryRecord.CONFIRMED:
            fortune.carry_confirmed = F('carry_confirmed') - self.carry_num
        fortune.save()

        self.status = CarryRecord.CANCEL
        self.save()


    def changePendingCarryAmount(self, new_value):
        """
        修改预计收益金额
        """
        if self.status != CarryRecord.PENDING:
            return

        delta = new_value - self.carry_num
        fortune = MamaFortune.objects.filter(mama_id=self.mama_id).first()
        fortune.carry_pending = F('carry_pending') + delta
        fortune.save()


    def carry_type_name(self):
        return get_choice_name(self.CARRY_TYPES, self.carry_type)

    def carry_num_display(self):
        return float('%.2f' % (self.carry_num * 0.01))

    carry_num_display.short_description = u"收益金额"

    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

    def is_carry_confirmed(self):
        return self.status == 2

    def is_carry_pending(self):
        return self.status == 1

    def is_carry_canceled(self):
        return self.status == 0

    def is_award_carry(self):
        return self.carry_type == 3

    def is_order_carry(self):
        return self.carry_type == 2

    def is_click_carry(self):
        return self.carry_type == 1


def carryrecord_update_mamafortune(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_carryrecord_update_mamafortune, task_carryrecord_update_dailystats

    transaction.on_commit(lambda: task_carryrecord_update_mamafortune(instance.mama_id))
    transaction.on_commit(lambda: task_carryrecord_update_dailystats(instance.mama_id, instance.date_field))

post_save.connect(carryrecord_update_mamafortune,
                  sender=CarryRecord, dispatch_uid='post_save_carryrecord_update_mamafortune')


def carryrecord_update_xiaolumama_active_hasale(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import carryrecord_update_xiaolumama_active_hasale
    if instance.mama and (not instance.mama.active):
        transaction.on_commit(lambda: carryrecord_update_xiaolumama_active_hasale(instance.mama_id))

post_save.connect(carryrecord_update_xiaolumama_active_hasale,
                  sender=CarryRecord, dispatch_uid='post_save_carryrecord_update_xiaolumama_active_hasale')


# def carryrecord_update_carrytotal(sender, instance, created, **kwargs):
#     from flashsale.xiaolumm.tasks_mama_carry_total import task_carryrecord_update_carrytotal
#     task_carryrecord_update_carrytotal.delay(instance.mama_id)
#
#
# post_save.connect(carryrecord_update_carrytotal,
#                   sender=CarryRecord, dispatch_uid='post_save_carryrecord_update_carrytotal')


def carryrecord_xlmm_newtask(sender, instance, **kwargs):
    """
    检测新手任务：完成第一笔点击收益
    """
    from flashsale.xiaolumm.tasks import task_push_new_mama_task
    from flashsale.xiaolumm.models.new_mama_task import NewMamaTask

    carryrecord = instance
    xlmm = carryrecord.mama
    if not xlmm:
        return

    if carryrecord.carry_type != CarryRecord.CR_CLICK:
        return

    is_exists = CarryRecord.objects.filter(mama_id=xlmm.id, carry_type=CarryRecord.CR_CLICK).exists()

    if not is_exists:
        params = {'money': '%.2f' % (int(carryrecord.carry_num) / 100.0)}
        task_push_new_mama_task.delay(xlmm, NewMamaTask.TASK_FIRST_CARRY, params=params)

pre_save.connect(carryrecord_xlmm_newtask,
                 sender=CarryRecord, dispatch_uid='pre_save_carryrecord_new_mama_task')


class OrderCarry(BaseModel):
    WAP_ORDER = 1
    APP_ORDER = 2
    REFERAL_ORDER = 3
    CARRY_TYPES = ((1, u'微商城订单'), (2, u'App订单额外+10%'), (3, u'下属订单+20%'),)
    STAGING = 0
    ESTIMATE = 1
    CONFIRM = 2
    CANCEL  = 3
    STATUS_TYPES = ((STAGING, u'待付款'), (ESTIMATE, u'预计收益'), (CONFIRM, u'确定收益'), (CANCEL, u'买家取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    order_id = models.CharField(max_length=64, db_index=True, blank=True, verbose_name=u'订单ID')
    order_value = models.IntegerField(default=0, verbose_name=u'订单金额')
    carry_num = models.IntegerField(default=0, verbose_name=u'提成金额')
    carry_type = models.IntegerField(default=1, choices=CARRY_TYPES, verbose_name=u'提成类型')  # 直接订单提成/粉丝订单提成/下属订单提成
    carry_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    sku_name = models.CharField(max_length=64, blank=True, verbose_name=u'sku名称')
    sku_img = models.CharField(max_length=256, blank=True, verbose_name=u'sku图片')
    contributor_nick = models.CharField(max_length=64, blank=True, verbose_name=u'贡献者昵称')
    contributor_img = models.CharField(max_length=256, blank=True, verbose_name=u'贡献者头像')
    contributor_id = models.BigIntegerField(default=0, verbose_name=u'贡献者ID')
    carry_plan_name = models.CharField(max_length=32, blank=True, verbose_name=u'佣金计划')
    agency_level = models.IntegerField(default=0, verbose_name=u'佣金级别')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')  #
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态')  # 待确定/已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_order_carry'
        app_label = 'xiaolumm'
        verbose_name = u'V2/订单提成'
        verbose_name_plural = u'V2/订单提成列表'

    def __unicode__(self):
        return '%s,%s,%s,%s' % (self.mama_id, self.carry_type, self.carry_num, self.date_field)

    def carry_type_name(self):
        # web order, we currently dont show name
        if self.carry_type == 1:
            return ''
        return get_choice_name(self.CARRY_TYPES, self.carry_type)

    def order_value_display(self):
        return '%.2f' % (self.order_value * 0.01)

    def carry_num_display(self):
        return float('%.2f' % (self.carry_num * 0.01))

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

    def contributor_nick_display(self):
        if self.contributor_nick == "":
            return u"匿名用户"
        return self.contributor_nick

    def is_pending(self):
        return self.status == 1

    def is_confirmed(self):
        return self.status == 2

    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None

    #def get_mama_customer(self):
    #    from flashsale.xiaolumm.models.models import XiaoluMama
    #    mama = XiaoluMama.objects.filter(id=self.mama_id).first()
    #    return mama.get_mama_customer()

    @property
    def mama(self):
        from flashsale.xiaolumm.models.models import XiaoluMama
        return XiaoluMama.objects.filter(id=self.mama_id).first()

    def is_direct_or_fans_carry(self):
        return self.carry_type == 1 or self.carry_type == 2


def commission_xlmm_newtask(sender, instance, **kwargs):
    """
    检测新手任务：赚取第一笔佣金
    """
    from flashsale.xiaolumm.tasks import task_push_new_mama_task
    from flashsale.xiaolumm.models.new_mama_task import NewMamaTask

    ordercarry = instance
    xlmm = ordercarry.mama
    if not xlmm:
        return
    ordercarry = OrderCarry.objects.filter(mama_id=xlmm.id).exists()

    if not ordercarry:
        task_push_new_mama_task.delay(xlmm, NewMamaTask.TASK_FIRST_COMMISSION)

pre_save.connect(commission_xlmm_newtask,
                 sender=OrderCarry, dispatch_uid='pre_save_commission_xlmm_newtask')


def ordercarry_update_carryrecord(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_ordercarry_update_carryrecord
    task_ordercarry_update_carryrecord.delay(instance)

post_save.connect(ordercarry_update_carryrecord,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_update_carryrecord')


def ordercarry_weixin_push(sender, instance, created, **kwargs):
    """
    订单提成推送到微信
    """
    if not created:
        return
    if instance.mama_id < 1:
        return
    from flashsale.xiaolumm.tasks.tasks_mama_push import task_weixin_push_ordercarry
    task_weixin_push_ordercarry.delay(instance)

post_save.connect(ordercarry_weixin_push,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_weixin_push')


def ordercarry_app_push(sender, instance, created, **kwargs):
    """
    """
    if not created:
        return
    from flashsale.xiaolumm.tasks import task_app_push_ordercarry
    task_app_push_ordercarry.delay(instance)

post_save.connect(ordercarry_app_push,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_app_push')


# 首单奖励
def ordercarry_send_first_award(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_first_order_send_award, task_update_mamafortune_hasale_num
    from flashsale.xiaolumm.models.models import XiaoluMama

    if not instance.mama:
        return

    if instance.mama.last_renew_type == XiaoluMama.TRIAL:
        task_first_order_send_award.delay(instance.mama)
    task_update_mamafortune_hasale_num.delay(instance.mama_id)

post_save.connect(ordercarry_send_first_award,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_send_first_alwad')


def ordercarry_update_ordercarry(sender, instance, created, **kwargs):
    if instance.is_direct_or_fans_carry():
        # find out parent mama_id, and this relationship must be established before the order creation date.
        referal_relationships = ReferalRelationship.objects.filter(referal_to_mama_id=instance.mama_id,
                                                                   created__lt=instance.created)
        from flashsale.xiaolumm.tasks import task_update_second_level_ordercarry, task_update_second_level_ordercarry_by_trial
        if referal_relationships.count() > 0:
            referal_relationship = referal_relationships[0]
            task_update_second_level_ordercarry.delay(referal_relationship, instance)
        else:
            # 看潜在关系列表
            from flashsale.xiaolumm.models import PotentialMama
            try:
                potential = PotentialMama.objects.filter(potential_mama=instance.mama_id).latest('created')
            except PotentialMama.DoesNotExist:
                return
            task_update_second_level_ordercarry_by_trial.delay(potential, instance)


post_save.connect(ordercarry_update_ordercarry,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_update_ordercarry')


def ordercarry_update_activevalue(sender, instance, created, **kwargs):
    if instance.carry_type == OrderCarry.WAP_ORDER or instance.carry_type == OrderCarry.APP_ORDER:
        from flashsale.xiaolumm.tasks import task_ordercarry_update_activevalue
        task_ordercarry_update_activevalue.delay(instance.uni_key)


post_save.connect(ordercarry_update_activevalue,
                  sender=OrderCarry, dispatch_uid='post_save_ordercarry_update_activevalue')


def ordercarry_update_order_number(sender, instance, created, **kwargs):
    mama_id = instance.mama_id
    date_field = instance.date_field

    from flashsale.xiaolumm.tasks import task_update_clickcarry_order_number, \
        task_update_mamafortune_order_num, task_ordercarry_increment_dailystats
    task_update_clickcarry_order_number.delay(mama_id, date_field)

    task_update_mamafortune_order_num.delay(mama_id)

    if created:
        task_ordercarry_increment_dailystats.delay(mama_id, date_field)


post_save.connect(ordercarry_update_order_number,
                  sender=OrderCarry, dispatch_uid='post_save_order_carry_update_order_number')


class AwardCarry(BaseModel):
    AWARD_OPEN_COURSE = 3
    AWARD_FIRST_ORDER = 5
    AWARD_SUBSCRIBE = 8
    AWARD_MAMA_SALE = 9
    AWARD_GROUP_SALE = 10
    AWARD_INVITE_FANS = 11
    AWARD_TYPES = ((1, u'直荐奖励'),(2, u'团队推荐奖励'),(3, u'授课奖金'),(4, u'新手任务'),
                   (5, u'首单奖励'),(6, u'推荐新手任务'),(7, u'一元邀请'),(8, u'关注公众号'),
                   (9, u'销售奖励'),(10, u'团队销售奖励') , (11, u'粉丝邀请'))
    STAGING = 1
    CONFIRMED = 2
    CANCEL = 3
    STATUS_TYPES = ((1, u'预计收益'), (2, u'确定收益'), (3, u'已取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    carry_num = models.IntegerField(default=0, verbose_name=u'奖励金额')
    carry_type = models.IntegerField(default=0, db_index=True, choices=AWARD_TYPES, verbose_name=u'奖励类型')  # 直接推荐奖励/团队成员奖励
    carry_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    contributor_nick = models.CharField(max_length=64, blank=True, null=True, verbose_name=u'贡献者昵称')
    contributor_img = models.CharField(max_length=256, blank=True, null=True, verbose_name=u'贡献者头像')
    contributor_mama_id = models.BigIntegerField(default=0, null=True, verbose_name=u'贡献者mama_id')
    carry_plan_name = models.CharField(max_length=32, blank=True, verbose_name=u'佣金计划')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID') #contributor_mama_id+award_type
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态')  # 待确定/已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_award_carry'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈邀请奖励'
        verbose_name_plural = u'V2/妈妈邀请奖励列表'

    def __unicode__(self):
        return '%s,%s,%s,%s' % (self.mama_id, self.carry_type, self.carry_num, self.date_field)

    def is_pending(self):
        return self.status == 1

    def is_confirmed(self):
        return self.status == 2

    def is_cancel(self):
        return self.status == 3

    def carry_type_name(self):
        return get_choice_name(self.AWARD_TYPES, self.carry_type)

    def carry_num_display(self):
        return float('%.2f' % (self.carry_num * 0.01))

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None

    @staticmethod
    def gen_uni_key(contributor_mama_id, award_type):
        return 'awardcarry-%s-%s' % (contributor_mama_id, award_type)

    @staticmethod
    def send_award(mama, num, name, description, uni_key, status, carry_type,
                   contributor_nick=None, contributor_img=None, contributor_mama_id=None):
        repeat_one = AwardCarry.objects.filter(uni_key=uni_key).first()
        if repeat_one:
            return repeat_one
        ac = AwardCarry(
            mama_id=mama.id,
            carry_num=num * 100,
            carry_type=carry_type,
            date_field=datetime.datetime.now().date(),
            carry_plan_name=name,
            carry_description=description,
            uni_key=uni_key,
            status=status,
            contributor_nick=contributor_nick if contributor_nick else mama.get_mama_customer().nick,
            contributor_img=contributor_img if contributor_img else mama.get_mama_customer().thumbnail,
            contributor_mama_id=contributor_mama_id if contributor_mama_id else mama.id
        )
        ac.save()
        return ac

    def cancel_award(self):
        self.status  = AwardCarry.CANCEL
        self.save()

    def confirm_award(self):
        self.status = AwardCarry.CONFIRMED
        self.save()

def awardcarry_update_carryrecord(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_awardcarry_update_carryrecord
    task_awardcarry_update_carryrecord.delay(instance)


post_save.connect(awardcarry_update_carryrecord,
                  sender=AwardCarry, dispatch_uid='post_save_awardcarry_update_carryrecord')


def awardcarry_weixin_push(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.carry_type == AwardCarry.AWARD_SUBSCRIBE or instance.carry_type == AwardCarry.AWARD_INVITE_FANS:
        # 关注公众号, 增加粉丝, 任务通知已发, 这里不用重复发送
        return
    from flashsale.xiaolumm.tasks import task_weixin_push_awardcarry
    if instance.mama_id > 0 and instance.status != 3:
        task_weixin_push_awardcarry.delay(instance)

post_save.connect(awardcarry_weixin_push,
                  sender=AwardCarry, dispatch_uid='post_save_awardcarry_weixin_push')


class ClickPlan(BaseModel):
    STATUS_TYPES = ((0, u'使用'), (1, u'取消'),)
    name = models.CharField(max_length=32, verbose_name=u'名字')

    # {"0":[10, 10], "1":[20, 60], "2":[30, 110], "3":[40, 160], "4":[50, 210], "5":[60, 260]}
    order_rules = JSONCharMyField(max_length=256, blank=True, default={}, verbose_name=u'规则')
    max_order_num = models.IntegerField(default=0, verbose_name=u'最大订单人数')

    start_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'生效时间')
    end_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'结束时间')

    status = models.IntegerField(default=0, choices=STATUS_TYPES, verbose_name=u'状态')
    default = models.BooleanField(default=False, verbose_name=u'缺省设置')

    class Meta:
        db_table = 'flashsale_xlmm_click_plan'
        app_label = 'xiaolumm'
        ordering = ['-created']
        verbose_name = u'V2/点击计划'
        verbose_name_plural = u'V2/点击计划列表'

    @classmethod
    def get_active_clickplan(cls):
        time_now = datetime.datetime.now()
        plan = cls.objects.filter(status=0, end_time__gte=time_now,
                                  start_time__lte=time_now).order_by('-created').first()
        if plan:
            return plan
        default = cls.objects.filter(status=0, default=True).first()
        return default


class ClickCarry(BaseModel):
    STATUS_TYPES = ((1, u'预计收益'), (2, u'确定收益'), (3, u'已取消'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    click_num = models.IntegerField(default=0, verbose_name=u'初始点击数')
    init_order_num = models.IntegerField(default=0, verbose_name=u'初始订单人数')
    init_click_price = models.IntegerField(default=0, verbose_name=u'初始点击价')
    init_click_limit = models.IntegerField(default=0, verbose_name=u'初始点击上限')
    confirmed_order_num = models.IntegerField(default=0, verbose_name=u'确定订单人数')
    confirmed_click_price = models.IntegerField(default=0, verbose_name=u'确定点击价')
    confirmed_click_limit = models.IntegerField(default=0, verbose_name=u'确定点击上限')
    carry_plan_name = models.CharField(max_length=32, blank=True, verbose_name=u'佣金计划')
    carry_plan_id = models.IntegerField(default=1, verbose_name=u'佣金计划ID')
    total_value = models.IntegerField(default=0, verbose_name=u'点击总价')
    carry_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')  # date+mama_id
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态')  # 待确定/已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_click_carry'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈点击返现'
        verbose_name_plural = u'V2/妈妈点击返现列表'

    def __unicode__(self):
        return '%s,%s' % (self.mama_id, self.total_value)

    def is_confirmed(self):
        return self.status == 2

    def init_click_price_display(self):
        return '%.2f' % (self.init_click_price * 0.01)

    def confirmed_click_price_display(self):
        return '%.2f' % (self.confirmed_click_price * 0.01)

    def total_value_display(self):
        return '%.2f' % (self.total_value * 0.01)

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None


def weixin_push_clickcarry(sender, instance, fake=False, **kwargs):
    from flashsale.xiaolumm.tasks import task_weixin_push_clickcarry
    task_weixin_push_clickcarry.delay(instance, fake=fake)

clickcarry_signal.connect(weixin_push_clickcarry, sender=ClickCarry, dispatch_uid='add_clickcarry_weixin_push')


def clickcarry_update_carryrecord(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_clickcarry_update_carryrecord
    task_clickcarry_update_carryrecord.delay(instance)


post_save.connect(clickcarry_update_carryrecord,
                  sender=ClickCarry, dispatch_uid='post_save_clickcarry_update_carryrecord')


def confirm_previous_clickcarry(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_confirm_previous_zero_order_clickcarry, \
        task_confirm_previous_order_clickcarry
    if created:
        mama_id = instance.mama_id
        date_field = instance.date_field
        task_confirm_previous_zero_order_clickcarry.delay(mama_id, date_field, 2)
        task_confirm_previous_order_clickcarry.delay(mama_id, date_field, 7)


post_save.connect(confirm_previous_clickcarry,
                  sender=ClickCarry, dispatch_uid='post_save_confirm_previous_clickcarry')


def gauge_active_mama(sender, instance, created, **kwargs):
    from django_statsd.clients import statsd
    if created:
        date_field = datetime.datetime.now().date()
        active_mama_count = ClickCarry.objects.filter(date_field=date_field).count()
        key = "clickcarry.active_mama"
        statsd.gauge(key, active_mama_count)


post_save.connect(gauge_active_mama, sender=ClickCarry, dispatch_uid='post_save_gauge_active_mama')


class ActiveValue(BaseModel):
    VALUE_MAP = {"1": 1, "2": 10, "3": 50, "4": 2}
    VALUE_TYPES = ((1, u'点击'), (2, u'订单'), (3, u'推荐'), (4, u'粉丝'),)
    STATUS_TYPES = ((1, u'待确定'), (2, u'已确定'), (3, u'已取消'), (4, u'已过期'),)

    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'小鹿妈妈id')
    value_num = models.IntegerField(default=0, verbose_name=u'活跃值')
    value_type = models.IntegerField(default=0, choices=VALUE_TYPES, verbose_name=u'类型')  # 点击/订单/推荐/粉丝
    value_description = models.CharField(max_length=64, blank=True, verbose_name=u'描述')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')  #
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    status = models.IntegerField(default=3, choices=STATUS_TYPES, verbose_name=u'状态')  # 待确定/已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_active_value_record'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈活跃值'
        verbose_name_plural = u'V2/妈妈活跃值列表'

    def __unicode__(self):
        return '%s,%s,%s' % (self.mama_id, self.value_type, self.value_num)

    def value_type_name(self):
        return get_choice_name(self.VALUE_TYPES, self.value_type)

    def status_display(self):
        return get_choice_name(self.STATUS_TYPES, self.status)

    def is_confirmed(self):
        return self.status == 2

    def today_carry(self):
        """
        this must exists to bypass serializer check
        """
        return None


def activevalue_update_mamafortune(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_activevalue_update_mamafortune
    mama_id = instance.mama_id
    task_activevalue_update_mamafortune.delay(mama_id)


post_save.connect(activevalue_update_mamafortune,
                  sender=ActiveValue, dispatch_uid='post_save_activevalue_update_mamafortune')


def confirm_previous_activevalue(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_confirm_previous_activevalue
    if created and instance.value_type == 1:
        mama_id = instance.mama_id
        date_field = instance.date_field
        task_confirm_previous_activevalue.delay(mama_id, date_field, 2)


post_save.connect(confirm_previous_activevalue,
                  sender=ActiveValue, dispatch_uid='post_save_confirm_previous_activevalue')


def activevalue_update_last_renew_time(sender, instance, created, **kwargs):
    if not created:
        return
    from flashsale.xiaolumm.models import XiaoluMama

    mama_id = instance.mama_id
    mama = XiaoluMama.objects.filter(id=mama_id,last_renew_type__gte=XiaoluMama.ELITE,status=XiaoluMama.EFFECT,charge_status=XiaoluMama.CHARGED).exclude(last_renew_type=XiaoluMama.HALF).first()
    if not mama:
        return

    start_date = datetime.date(2016,8,28) # start from 2016-08-28
    charge_date = mama.charge_time.date()
    if charge_date > start_date:
        start_date = charge_date
    today = datetime.date.today()

    cnt = ActiveValue.objects.filter(mama_id=mama_id,date_field__gte=start_date,date_field__lt=today).values('date_field').distinct().count()
    if today == instance.date_field:
        cnt += 1

    renew_date = start_date + datetime.timedelta(days=365+cnt)
    renew_time = datetime.datetime(renew_date.year, renew_date.month, renew_date.day)
    if mama.renew_time != renew_time:
        mama.renew_time = renew_time
        mama.save(update_fields=['renew_time', 'modified'])

post_save.connect(activevalue_update_last_renew_time,
                  sender=ActiveValue, dispatch_uid='post_save_activevalue_update_last_renew_time')


class ReferalRelationship(BaseModel):
    """
    xiaolu mama referal relationship
    """
    VALID = 1
    INVALID = 2
    STATUS_TYPES = ((VALID, u'有效'), (INVALID, u'无效'))
    referal_from_grandma_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'妈妈的妈妈id')
    referal_from_mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'妈妈id')
    referal_to_mama_id = models.BigIntegerField(default=0, unique=True, verbose_name=u'被推荐妈妈id')
    referal_to_mama_nick = models.CharField(max_length=64, blank=True, verbose_name=u'被推荐者昵称')
    referal_to_mama_img = models.CharField(max_length=256, blank=True, verbose_name=u'被推荐者头像')
    order_id = models.CharField(max_length=64, blank=True, verbose_name=u'订单ID')
    referal_type = models.IntegerField(choices=XiaoluMama.RENEW_TYPE, default=XiaoluMama.FULL, db_index=True, verbose_name=u"类型")
    status = models.IntegerField(default=VALID, choices=STATUS_TYPES, db_index=True, verbose_name=u'状态')  # 已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_referal_relationship'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈推荐关系'
        verbose_name_plural = u'V2/妈妈推荐关系列表'

    @property
    def to_mama_mobile(self):
        from flashsale.xiaolumm.models import XiaoluMama
        from flashsale.pay.models import Customer

        mama = XiaoluMama.objects.filter(id=self.referal_to_mama_id).first()
        if mama:
            customer = Customer.objects.filter(unionid=mama.unionid).first()
            if customer and customer.mobile:
                return customer.mobile
        return None

    def is_confirmed(self):
        return self.referal_type == XiaoluMama.FULL or self.referal_type == XiaoluMama.HALF or self.referal_type == XiaoluMama.ELITE

    def referal_to_mama_nick_display(self):
        if self.referal_to_mama_nick == "":
            return u"匿名用户"
        return self.referal_to_mama_nick

    @classmethod
    def get_ship_chain(cls, to_mama_id, from_mama_id):
        # type: (int, int) -> List[int]
        """妈妈 推荐 关系链 (上级妈妈 在 列表前面)
        """
        chain = []
        c_count = 0
        while to_mama_id != from_mama_id:
            ship = ReferalRelationship.objects.filter(referal_to_mama_id=to_mama_id,
                                                      status=ReferalRelationship.VALID).first()
            to_mama_id = ship.referal_from_mama_id
            chain.insert(0, to_mama_id)
            c_count += 1
            if c_count >= 10:
                break
        return chain

    @staticmethod
    def get_referal_dict(mama_ids):
        rr = ReferalRelationship.objects.filter(referal_from_mama_id__in=mama_ids).values_list('referal_from_mama_id', 'referal_to_mama_id')
        res = {}
        for line in rr:
            res[line[0]] = res.get(line[0], []) + [line[1]]
        return res

    def get_referal_award(self):
        """ 获取妈妈的推荐红包 """
        award_carrys = AwardCarry.objects.filter(mama_id=self.referal_from_mama_id,
                                                 contributor_mama_id=self.referal_to_mama_id)
        if award_carrys.exists():
            award_carry = award_carrys[0]
            return award_carry
        else:
            return None

    def update_referal_relationship(self, potential_record):
        referal_type = potential_record.last_renew_type
        if self.is_confirmed() and self.referal_type > referal_type:
            # We dont do update if referalrelationship is confirmed and referal_type is higher.
            return

        order_id = potential_record.extras.get('oid') or None
        if not order_id:
            order_id = potential_record.extras.get('cashout_id') or ''
            order_id = '_'.join(['cashout_id', str(order_id)])

        logmsg = '%s|%s|%s|%s' % (self.referal_from_grandma_id, self.referal_from_mama_id, self.referal_type, self.order_id)
        update_fields = []
        if self.referal_from_mama_id != potential_record.referal_mama:
            referal_from_grandma_id = 0
            rr = ReferalRelationship.objects.filter(referal_to_mama_id=potential_record.referal_mama).first()
            if rr:
                referal_from_grandma_id = rr.referal_from_mama_id
            self.referal_from_grandma_id = referal_from_grandma_id
            update_fields.append('referal_from_grandma_id')
            self.referal_from_mama_id = potential_record.referal_mama
            update_fields.append('referal_from_mama_id')

        if self.referal_type != referal_type:
            self.referal_type = referal_type
            update_fields.append('referal_type')
        if self.order_id != order_id:
            self.order_id = order_id
            update_fields.append('order_id')
        if update_fields:
            self.save(update_fields=update_fields)

            from core.options import log_action, CHANGE, get_systemoa_user
            sys_oa = get_systemoa_user()
            log_action(sys_oa, self, CHANGE, logmsg)

            return True
        return False

    @classmethod
    def create_relationship_by_potential(cls, potential_record):
        """ 通过潜在妈妈列表中的记录创建推荐关系 """
        # 先查看是否有推荐关系存在(被推荐人　potential_record.potential_mama 潜在妈妈)

        order_id = potential_record.extras.get('oid') or None
        if not order_id:
            order_id = potential_record.extras.get('cashout_id') or ''
            order_id = '_'.join(['cashout_id', str(order_id)])

        referal_from_grandma_id = 0
        rr = ReferalRelationship.objects.filter(referal_to_mama_id=potential_record.referal_mama).first()
        if rr:
            referal_from_grandma_id = rr.referal_from_mama_id

        ship = cls(referal_from_grandma_id=referal_from_grandma_id,
                   referal_from_mama_id=potential_record.referal_mama,
                   referal_to_mama_id=potential_record.potential_mama,
                   referal_to_mama_nick=potential_record.nick,
                   referal_type=potential_record.last_renew_type,
                   order_id=order_id,
                   referal_to_mama_img=potential_record.thumbnail)
        ship.save()
        return ship

    def change_referal_mama(self, upper_mama_id, is_elite=False):
        # type: (int) -> bool
        """更换上级妈妈
        """
        from ..apis.v1.relationship import get_relationship_by_mama_id
        update_fields = []
        if self.referal_from_mama_id != upper_mama_id:
            self.referal_from_mama_id = upper_mama_id
            update_fields.append('referal_from_mama_id')

        upper_mama_relationship = get_relationship_by_mama_id(upper_mama_id)
        grand_mama_id = upper_mama_relationship.referal_from_mama_id if upper_mama_relationship else 0
        if self.referal_from_grandma_id != grand_mama_id:
            self.referal_from_grandma_id = grand_mama_id
            update_fields.append('referal_from_grandma_id')

        if update_fields:  # 说明有更换上级
            if is_elite:  # 是否是更新为精英妈妈
                self.referal_type = XiaoluMama.ELITE
                update_fields.append('referal_type')
            update_fields.append('modified')
            self.save(update_fields=update_fields)
            return True
        return False


def referalrelationship_xlmm_newtask(sender, instance, **kwargs):
    """
    检测新手任务：发展第一个代理　
    """
    from flashsale.xiaolumm.tasks import task_push_new_mama_task
    from flashsale.xiaolumm.models.new_mama_task import NewMamaTask
    from flashsale.xiaolumm.models.models import PotentialMama, XiaoluMama

    referal_relationship = instance
    xlmm_id = referal_relationship.referal_from_mama_id
    xlmm = XiaoluMama.objects.filter(id=xlmm_id).first()

    item = PotentialMama.objects.filter(referal_mama=xlmm_id).exists() or \
        ReferalRelationship.objects.filter(referal_from_mama_id=xlmm_id).exists()

    if not item:
        task_push_new_mama_task.delay(xlmm, NewMamaTask.TASK_FIRST_MAMA_RECOMMEND)

pre_save.connect(referalrelationship_xlmm_newtask,
                 sender=ReferalRelationship, dispatch_uid='pre_save_referalrelationship_xlmm_newtask')


def update_mamafortune_invite_num(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_update_mamafortune_invite_num

    mama_id = instance.referal_from_mama_id
    task_update_mamafortune_invite_num.delay(mama_id)


post_save.connect(update_mamafortune_invite_num,
                  sender=ReferalRelationship, dispatch_uid='post_save_update_mamafortune_invite_num')


def update_mamafortune_mama_level(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks import task_update_mamafortune_mama_level
    task_update_mamafortune_mama_level.delay(instance)

post_save.connect(update_mamafortune_mama_level,
                  sender=ReferalRelationship, dispatch_uid='post_save_update_mamafortune_mama_level')


def update_mama_fans(sender, instance, created, **kwargs):
    if not created:
        return

    from flashsale.xiaolumm.models import XiaoluMama
    from flashsale.xiaolumm.models import XlmmFans

    mama = XiaoluMama.objects.filter(id=instance.referal_to_mama_id).first()
    if not mama:
        return

    customer = mama.get_mama_customer()
    fans_cusid = customer.id
    fans_nick = customer.nick
    fans_thumbnail = customer.thumbnail

    fan = XlmmFans.objects.filter(fans_cusid=fans_cusid).first()
    if fan:
        return

    from_mama_id = instance.referal_from_mama_id
    from_mama = XiaoluMama.objects.filter(id=from_mama_id).first()
    if not from_mama:
        return
    from_customer = from_mama.get_mama_customer()
    if not from_customer:
        return
    xlmm_cusid = from_customer.id
    fan = XlmmFans(xlmm=from_mama_id, xlmm_cusid=xlmm_cusid, refreal_cusid=xlmm_cusid, fans_cusid=fans_cusid,
                   fans_nick=fans_nick, fans_thumbnail=fans_thumbnail)
    fan.save()

post_save.connect(update_mama_fans, sender=ReferalRelationship, dispatch_uid='post_save_update_mama_fans')


def referal_update_activevalue(sender, instance, created, **kwargs):
    if not created:
        return
    from flashsale.xiaolumm.tasks import task_referal_update_activevalue
    mama_id = instance.referal_from_mama_id
    date_field = instance.created.date()
    contributor_id = instance.referal_to_mama_id
    task_referal_update_activevalue.delay(mama_id, date_field, contributor_id)


post_save.connect(referal_update_activevalue,
                  sender=ReferalRelationship, dispatch_uid='post_save_referal_update_activevalue')


def update_referal_awardcarry(sender, instance, created, **kwargs):
    if instance.created.date() > MAMA_FORTUNE_HISTORY_LAST_DAY:
        from flashsale.xiaolumm.tasks import task_referal_update_awardcarry
        task_referal_update_awardcarry.delay(instance)


post_save.connect(update_referal_awardcarry,
                  sender=ReferalRelationship, dispatch_uid='post_save_update_referal_awardcarry')


def update_group_awardcarry(sender, instance, created, **kwargs):
    if instance.created.date() > MAMA_FORTUNE_HISTORY_LAST_DAY:
        from flashsale.xiaolumm.tasks import task_update_group_awardcarry
        task_update_group_awardcarry.delay(instance)

post_save.connect(update_group_awardcarry,
                  sender=ReferalRelationship, dispatch_uid='post_save_update_group_awardcarry')


class GroupRelationship(BaseModel):
    """
    xiaolu mama group relationship
    """
    leader_mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'领队妈妈id')
    referal_from_mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'推荐妈妈id')
    member_mama_id = models.BigIntegerField(default=0, unique=True, verbose_name=u'成员妈妈id')
    member_mama_nick = models.CharField(max_length=64, blank=True, verbose_name=u'贡献者昵称')
    member_mama_img = models.CharField(max_length=256, blank=True, verbose_name=u'贡献者头像')
    referal_type = models.IntegerField(choices=XiaoluMama.RENEW_TYPE, default=XiaoluMama.FULL, db_index=True, verbose_name=u"类型")
    status = models.IntegerField(default=1, choices=ReferalRelationship.STATUS_TYPES, db_index=True, verbose_name=u'状态')  # 已确定/取消

    class Meta:
        db_table = 'flashsale_xlmm_group_relationship'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈团队关系'
        verbose_name_plural = u'V2/妈妈团队关系列表'


class UniqueVisitor(BaseModel):
    mama_id = models.BigIntegerField(default=0, db_index=True, verbose_name=u'妈妈id')
    visitor_unionid = models.CharField(max_length=64, verbose_name=u"访客UnionID")
    visitor_nick = models.CharField(max_length=64, blank=True, verbose_name=u'访客昵称')
    visitor_img = models.CharField(max_length=256, blank=True, verbose_name=u'访客头像')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')  # unionid+date
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')

    class Meta:
        db_table = 'flashsale_xlmm_unique_visitor'
        app_label = 'xiaolumm'
        verbose_name = u'V2/独立访客'
        verbose_name_plural = u'V2/独立访客列表'

    def visitor_description(self):
        return u"来自微信点击访问"

    def nick_display(self):
        if self.visitor_nick == '':
            return u"匿名用户"
        return self.visitor_nick


def visitor_update_clickcarry_and_activevalue(sender, instance, created, **kwargs):
    """
    访客更新点击收益和活跃值
    """
    if not created:
        return

    mama_id = instance.mama_id
    date_field = instance.date_field
    is_fake = instance.uni_key.startswith('fake')  # 是否伪造访客

    try:
        from flashsale.xiaolumm.models import XiaoluMama
        mama = XiaoluMama.objects.get(id=mama_id)
        if not mama.is_click_countable():
            return
    except XiaoluMama.DoesNotExist:
        return

    from flashsale.xiaolumm.tasks import task_visitor_increment_clickcarry
    task_visitor_increment_clickcarry.delay(mama_id, date_field, fake=is_fake)

    from flashsale.xiaolumm.tasks import task_visitor_increment_activevalue
    task_visitor_increment_activevalue.delay(mama_id, date_field)

    from flashsale.xiaolumm.tasks import task_visitor_increment_dailystats
    task_visitor_increment_dailystats.delay(mama_id, date_field)


post_save.connect(visitor_update_clickcarry_and_activevalue,
                  sender=UniqueVisitor, dispatch_uid='post_save_visitor_update_clickcarry_and_activevalue')



class MamaDailyAppVisit(BaseModel):
    DEVICE_UNKNOWN = 0
    DEVICE_ANDROID = 1
    DEVICE_IOS = 2
    DEVICE_MOZILLA = 3

    DEVICE_TYPES = ((DEVICE_UNKNOWN, 'Unknown'), (DEVICE_ANDROID, 'Android'), (DEVICE_IOS, 'IOS'), (DEVICE_MOZILLA, '浏览器'))

    mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'妈妈id')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')  # mama_id+date
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
    device_type = models.IntegerField(default=0, choices=DEVICE_TYPES, db_index=True, verbose_name=u'设备')
    version = models.CharField(max_length=32, blank=True, verbose_name=u'版本信息')
    user_agent = models.CharField(max_length=128, blank=True, verbose_name=u'UserAgent')
    num_visits = models.IntegerField(default=1, verbose_name=u'访问次数')
    renew_type = models.IntegerField(default=0, choices=XiaoluMama.RENEW_TYPE, db_index=True, verbose_name=u'妈妈类型')

    class Meta:
        db_table = 'flashsale_xlmm_mamadailyappvisit'
        app_label = 'xiaolumm'
        index_together = ['date_field', 'version', 'renew_type']
        verbose_name = u'V2/妈妈app访问'
        verbose_name_plural = u'V2/妈妈app访问列表'

    @staticmethod
    def gen_uni_key(mama_id, date_field, device_type):
        return '%s-%s-%s' % (mama_id, date_field, device_type)

    def get_user_version(self):
        from flashsale.apprelease.models import AppRelease
        if self.device_type == AppRelease.DEVICE_ANDROID:
            version_code = self.version
            version = AppRelease.get_version_info(self.device_type, version_code)
            return version # Android
        return self.version #IOS

    def get_latest_version(self):
        from flashsale.apprelease.models import AppRelease
        version = AppRelease.get_latest_version(self.device_type)
        return version

#def mama_daily_app_visit_stats(sender, instance, created, **kwargs):
#    if not created:
#        return
#
#    from django_statsd.clients import statsd
#    today_date = datetime.date.today()
#    visit_count = MamaDailyAppVisit.objects.filter(date_field=today_date).count()
#    key = "mama.daily_app_visit"
#    statsd.timing(key, visit_count)
#
#post_save.connect(mama_daily_app_visit_stats,
#                  sender=MamaDailyAppVisit, dispatch_uid='post_save_mama_daily_app_visit_stats')


def mama_app_version_check(sender, instance, created, **kwargs):
    if not created:
        return

    from flashsale.xiaolumm.tasks import task_weixin_push_update_app
    task_weixin_push_update_app.delay(instance)

post_save.connect(mama_app_version_check,
                  sender=MamaDailyAppVisit, dispatch_uid='post_save_mama_app_version_check')


def mama_update_device_stats(sender, instance, created, **kwargs):
    if not created:
        return

    from flashsale.xiaolumm.models import MamaDeviceStats
    from flashsale.apprelease.models import AppRelease

    device_type = instance.device_type
    date_field = instance.date_field
    renew_type = instance.renew_type

    latest_version = instance.get_latest_version()
    if device_type == MamaDailyAppVisit.DEVICE_ANDROID:
        latest_version = AppRelease.get_latest_version_code(device_type)

    uni_key = MamaDeviceStats.gen_uni_key(device_type, date_field, renew_type)

    md = MamaDeviceStats.objects.filter(uni_key=uni_key).first()
    if not md:
        md = MamaDeviceStats(device_type=device_type, uni_key=uni_key, date_field=date_field, renew_type=renew_type)
        md.save()

    if (md.num_latest + md.num_outdated) % 100 == 0:
        # Every 100 creation, we do this counting.
        md.num_latest = MamaDailyAppVisit.objects.filter(date_field=date_field,device_type=device_type,renew_type=renew_type,version=latest_version).count()
        md.num_outdated = MamaDailyAppVisit.objects.filter(date_field=date_field,device_type=device_type,renew_type=renew_type,version__lt=latest_version).count()
        visits_sum = MamaDailyAppVisit.objects.filter(date_field=date_field,device_type=device_type,renew_type=renew_type).aggregate(n=Sum('num_visits'))
        md.num_visits = visits_sum.get('n') or 0
        md.save(update_fields=['num_latest', 'num_outdated', 'num_visits'])
    else:
        update_fields = []
        if latest_version == instance.version:
            md.num_latest = md.num_latest + 1
            update_fields.append('num_latest')
        else:
            md.num_outdated = md.num_outdated + 1
            update_fields.append('num_outdated')
        md.num_visits = md.num_visits + 1
        update_fields.append('num_visits')
        md.save(update_fields=update_fields)

post_save.connect(mama_update_device_stats,
                  sender=MamaDailyAppVisit, dispatch_uid='post_save_mama_update_device_stats')
