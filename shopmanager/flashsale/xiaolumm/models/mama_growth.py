# coding=utf-8
import datetime
from django.db import models
from django.db.models import Sum, Count

from core.models import BaseModel
from core.utils import week_range

from flashsale.xiaolumm.utils import get_award_carry_num
from flashsale.xiaolumm import constants

import logging
logger = logging.getLogger(__name__)

def get_mama_week_sale_amount(mamaid_list, week_start, week_end):
    from flashsale.xiaolumm.models import OrderCarry
    order_carrys = OrderCarry.objects.filter(
        date_field__range=(week_start, week_end), mama_id__in=mamaid_list,
        status__in=(OrderCarry.ESTIMATE, OrderCarry.CONFIRM))
    return sum(order_carrys.values_list('order_value', flat=True))

class MamaMission(BaseModel):
    TARGET_PERSONAL = 'personal'
    TARGET_GROUP    = 'group'
    TARGET_CHOICES  = (
        (TARGET_PERSONAL, u'个人'),
        (TARGET_GROUP, u'团队')
    )

    KPI_COUNT = 'count'
    KPI_AMOUNT = 'amount'
    KPI_CHOICES = (
        (KPI_COUNT, u'计数'),
        (KPI_AMOUNT, u'金额')
    )

    TYPE_WEEKLY   = 'weekly'
    TYPE_DEADLINE = 'deadline'
    TYPE_MOUNTHLY = 'monthly'
    TYPE_ONCETIME = 'oncetime'
    TYPE_CHOICES = (
        (TYPE_WEEKLY, u'周任务'),
        (TYPE_MOUNTHLY, u'月任务'),
        (TYPE_ONCETIME, u'一次性任务'),
        (TYPE_DEADLINE, u'DEADLINE'),
    )

    DRAFT    = 'draft'
    PROGRESS = 'progress'
    FINISHED = 'finished'
    CANCEL   = 'cancel'
    STATUS_CHOICES = (
        (DRAFT, u'草稿'),
        (PROGRESS, u'进行中'),
        (FINISHED, u'已结束'),
        (CANCEL, u'已取消'),
    )
    CAT_SALE_MAMA   = 'sale_mama'
    CAT_SALE_GROUP  = 'sale_group'
    CAT_REFER_MAMA  = 'refer_mama'
    CAT_GROUP_MAMA  = 'group_refer'
    CAT_FIRST_ORDER = 'first_order'
    CAT_OPEN_COURSE = 'open_course'
    CAT_JOIN_GUIDE  = 'join_guide'
    CAT_TRIAL_MAMA  = 'trial_mama'
    CAT_REFER_GUIDE = 'refer_guide'
    CATEGORY_TYPES  = (
        (CAT_SALE_MAMA, u'个人销售'),
        (CAT_SALE_GROUP, u'团队销售'),
        (CAT_REFER_MAMA, u'新增下属妈妈'),
        (CAT_GROUP_MAMA, u'新增团队妈妈'),
        (CAT_FIRST_ORDER, u'首单奖励'),
        (CAT_OPEN_COURSE, u'授课奖金'),
        (CAT_JOIN_GUIDE, u'新手任务'),
        (CAT_TRIAL_MAMA, u'邀请妈妈试用开店'),
        (CAT_REFER_GUIDE, u'新手指导')
    )

    name   = models.CharField(max_length=64, verbose_name=u'任务名称')
    target = models.CharField(max_length=8, default=TARGET_PERSONAL,
                              choices=TARGET_CHOICES, verbose_name=u'任务对象')

    cat_type = models.CharField(max_length=16, default=CAT_SALE_MAMA,
                                 choices=CATEGORY_TYPES, db_index=True, verbose_name=u'任务类型')
    kpi_type = models.CharField(max_length=8, default=KPI_COUNT,
                                choices=KPI_CHOICES, verbose_name=u'考核方式')

    target_value = models.IntegerField(default=0, verbose_name=u'任务达标数')
    award_amount = models.IntegerField(default=0, verbose_name=u'达标奖励(分)')

    start_time   = models.DateTimeField(null=True, blank=True, verbose_name=u'开始时间')
    end_time     = models.DateTimeField(null=True, blank=True, verbose_name=u'结束时间')
    date_type    = models.CharField(max_length=8, default=TYPE_WEEKLY,
                                choices=TYPE_CHOICES, verbose_name=u'任务周期')
    desc   = models.TextField(blank=True, null=True, verbose_name=u'任务描述')
    status = models.CharField(max_length=8, choices=STATUS_CHOICES,
                              default=DRAFT, verbose_name=u'状态')

    class Meta:
        db_table = 'flashsale_xlmm_mission'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈周激励任务'
        verbose_name_plural = u'V2/妈妈周激励任务列表'

    def __unicode__(self):
        return '<%s, %s>' %(self.id, self.name)

    def is_receivable(self):
        """ 任务是否可以接收 """
        return self.status == MamaMission.PROGRESS

    def get_mama_target_value(self, xiaolumama, day_datetime):
        """
            若妈妈上周未完成目标，则上周目标继续,　若连续两周及以上未完成目标，则将目标下调一个等级
        """
        from flashsale.xiaolumm.models import GroupRelationship, ReferalRelationship, XiaoluMama

        def _find_target_value(target_stages, finish_value):
            for k1, k2, t in target_stages:
                if k1 <= finish_value < k2 or finish_value >= k2:
                    return t * 100
            return 10000

        last_week_daytime = day_datetime - datetime.timedelta(days=7)
        week_start , week_end = week_range(last_week_daytime)
        if self.kpi_type == self.KPI_AMOUNT:
            if self.target == self.TARGET_PERSONAL:
                mama_ids = [xiaolumama.id]
                target_stages = constants.PERSONAL_TARGET_STAGE
                award_rate = 15 * 100
            else :
                group_mamas = GroupRelationship.objects.filter(leader_mama_id=xiaolumama.id)
                mama_ids = group_mamas.values_list('member_mama_id', flat=True)
                target_stages = constants.GROUP_TARGET_STAGE
                award_rate = 50 * 100

            last_1st_week = last_week_daytime.strftime('%Y-%m-%d')
            mama_1st_record = MamaMissionRecord.objects.filter(
                mission=self,
                year_week=last_1st_week,
                mama_id=xiaolumama.id
            ).first()

            last_week_finish_value = get_mama_week_sale_amount(mama_ids, week_start, week_end) / 100
            if mama_1st_record and not mama_1st_record.is_finished():
                last_2th_week = (last_week_daytime -  datetime.timedelta(days=7)).strftime('%Y-%m-%d')
                mama_2th_record = MamaMissionRecord.objects.filter(
                    mission=self,
                    year_week=last_2th_week,
                    mama_id=xiaolumama.id
                ).first()
                # 若两周连续不达标, 则调整妈妈目标数
                if mama_2th_record and not mama_2th_record.is_finished():
                    target_value = _find_target_value(target_stages, last_week_finish_value)
                    return min(target_value, mama_1st_record.target_value), award_rate
                return mama_1st_record.target_value, award_rate

            return _find_target_value(target_stages, last_week_finish_value), award_rate

        if self.cat_type == MamaMission.CAT_REFER_MAMA:
            last_referal_num = ReferalRelationship.objects.filter(referal_from_mama_id=xiaolumama.id,
                                                                  status=ReferalRelationship.VALID).count()
            return self.target_value, get_award_carry_num(last_referal_num, XiaoluMama.FULL)

        return self.target_value, self.award_amount


def gen_mama_mission_record_unikey(mission_id, year_week, mama_id):
    return '%d-%s-%d'%(int(mission_id), year_week, int(mama_id))

class MamaMissionRecord(BaseModel):

    STAGING  = 'staging'
    FINISHED = 'finished'
    CLOSE    = 'close'
    STATUS_CHOICES = (
        (STAGING, u'进行中'),
        (FINISHED, u'已完成'),
        (CLOSE, u'未完成')
    )

    mission = models.ForeignKey(MamaMission, verbose_name=u'关联任务')
    mama_id = models.IntegerField(default=0, verbose_name=u'妈妈id')
    referal_from_mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'推荐人id')
    group_leader_mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'团队队长id')
    year_week = models.CharField(max_length=16, blank=True, db_index=True, verbose_name=u'年-周') #2016-32

    target_value = models.IntegerField(default=0, verbose_name=u'目标值')
    finish_value = models.IntegerField(default=0, verbose_name=u'完成值')
    award_amount = models.IntegerField(default=0, verbose_name=u'奖励(分)')
    finish_time  = models.DateTimeField(blank=True, db_index=True, null=True, verbose_name=u'完成时间')

    uni_key  = models.CharField(max_length=32, unique=True, verbose_name=u'唯一约束') #mission_id + year_week + mama_id
    status = models.CharField(max_length=8, default=STAGING,choices=STATUS_CHOICES, db_index=True, verbose_name=u'状态')
    
    class Meta:
        db_table = 'flashsale_xlmm_missionrecord'
        index_together = [('mama_id', 'year_week', 'mission')]
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈周激励任务记录'
        verbose_name_plural = u'V2/妈妈周激励任务记录列表'

    def __unicode__(self):
        return '<%s, %s, %s>' % (self.mama_id, self.year_week, self.mission)

    def save(self, *args, **kwargs):
        if not self.uni_key:
            self.uni_key = gen_mama_mission_record_unikey(self.mission.id, self.year_week, self.mama_id)
            logger.debug('generate mission unikey: %s'%self.uni_key)
        super(MamaMissionRecord, self).save(*args, **kwargs)

    @staticmethod
    def gen_week_field(self, date_time):
        ic = date_time.isocalendar()
        return "%s-week-%s" % (ic[0], ic[1])

    def is_finished(self):
        return self.status == self.FINISHED

    def is_staging(self):
        return self.status == self.STAGING

    def get_finish_value(self):
        if self.mission.kpi_type == MamaMission.KPI_AMOUNT:
            return self.finish_value / 100.0
        return self.finish_value

    def get_target_value(self):
        if self.mission.kpi_type == MamaMission.KPI_AMOUNT:
            return self.target_value / 100.0
        return self.target_value

    def get_award_amount(self):
        return self.award_amount / 100.0

    def get_group_finish_value(self):
        if self.mission.target != MamaMission.TARGET_GROUP:
            return 0
        if not hasattr(self, '_group_finish_value_'):
            group_records = MamaMissionRecord.objects.filter(group_leader_mama_id=self.group_leader_mama_id,
                                                             mission=self.mission,
                                                             year_week=self.year_week)
            self._group_finish_value_ = sum(group_records.values_list('finish_value', flat=True))
        return self._group_finish_value_

    def gen_uni_key(self):
        return '{0}-{1}-{2}'.format('weeklyaward' ,self.mama_id, self.id)

    def update_mission_value(self, finish_value):
        # TODO@meron 如果任务中订单金额退款，任务完成状态需要变更？
        self.finish_value = int(finish_value)
        cur_year_week = datetime.datetime.now().strftime('%Y-%W')
        if self.finish_value >= self.target_value and self.is_staging():
            self.status = self.FINISHED
            self.finish_time = datetime.datetime.now()
            self.save(update_fields=['finish_value', 'status', 'finish_time'])
            # 妈妈邀请任务奖励已经单独发放, 该处值发放团队奖励, 妈妈销售奖励, 团队销售奖励
            if self.mission.kpi_type == MamaMission.KPI_AMOUNT \
                    or self.mission.target == MamaMission.TARGET_GROUP:
                from flashsale.xiaolumm.tasks import task_send_mama_weekly_award
                task_send_mama_weekly_award.delay(self.mama_id, self.id)

        elif self.finish_value < self.target_value and self.is_finished():
            self.status = self.STAGING
            self.finish_time = datetime.datetime.now()
            self.save(update_fields=['finish_value', 'status', 'finish_time'])
            if self.mission.kpi_type == MamaMission.KPI_AMOUNT \
                    or self.mission.target == MamaMission.TARGET_GROUP:
                from flashsale.xiaolumm.tasks import task_cancel_mama_weekly_award
                task_cancel_mama_weekly_award.delay(self.mama_id, self.id)

        elif cur_year_week > self.year_week and self.is_staging():
            self.status = self.CLOSE
            self.finish_time = None
            self.save(update_fields=['finish_value', 'status', 'finish_time'])



from flashsale.xiaolumm.signals import signal_xiaolumama_register_success
from flashsale.pay.signals import signal_saletrade_pay_confirm, signal_saletrade_refund_confirm

def mama_register_update_mission_record(sender, xiaolumama, renew, *args, **kwargs):
    """ 妈妈注册成功更新推荐妈妈激励状态 """
    try:
        logger.info('mama_register_update_mission_record start: mama=%s, renew=%s'%(xiaolumama, renew))
        from flashsale.xiaolumm.models import XiaoluMama, ReferalRelationship, PotentialMama, GroupRelationship
        parent_mama_ids = xiaolumama.get_parent_mama_ids()
        if not parent_mama_ids or renew:
            return

        parent_mama_id = parent_mama_ids[0]
        week_start, week_end = week_range(xiaolumama.charge_time)
        year_week = xiaolumama.charge_time.strftime('%Y-%W')

        base_missions = MamaMissionRecord.objects.filter(year_week=year_week, mama_id=parent_mama_id)
        if xiaolumama.last_renew_type == XiaoluMama.TRIAL:
            # 一元妈妈邀请数
            total_mama_count = PotentialMama.objects.filter(
                created__range=(week_start, week_end),
                referal_mama=parent_mama_id) \
                .aggregate(mama_count=Count('potential_mama')).get('mama_count')
            mission_record = base_missions.filter(
                mission__target=MamaMission.TARGET_PERSONAL,
                mission__cat_type= MamaMission.CAT_TRIAL_MAMA, # MamaMission.CAT_REFER_MAMA,
            ).order_by('-status').first()
            if mission_record:
                mission_record.update_mission_value(total_mama_count)
        else:
            # 正式妈妈邀请数
            total_mama_count = ReferalRelationship.objects.filter(
                created__range=(week_start, week_end),
                status=ReferalRelationship.VALID,
                referal_from_mama_id=parent_mama_id)\
                .aggregate(mama_count=Count('referal_to_mama_id')).get('mama_count')
            mission_record = base_missions.filter(
                mission__target=MamaMission.TARGET_PERSONAL,
                mission__cat_type=MamaMission.CAT_REFER_MAMA,
            ).order_by('-status').first()
            if mission_record:
                mission_record.update_mission_value(total_mama_count)
        print 'total_mama_count:',xiaolumama, mission_record, total_mama_count
        from flashsale.xiaolumm.tasks import task_create_or_update_mama_mission_state
        task_create_or_update_mama_mission_state.delay(parent_mama_id)

        logger.info('mama_register_update_mission_record end: %s' % xiaolumama)
    except Exception, exc:
        logger.error('mama_register_update_mission_record error: mama_id=%s, %s'%(xiaolumama.id ,exc), exc_info=True)

signal_xiaolumama_register_success.connect(mama_register_update_mission_record,
                                           dispatch_uid='post_save_mama_register_update_mission_record')

def _update_mama_salepayment_mission_record(sale_trade):
    from flashsale.xiaolumm.models import XiaoluMama, OrderCarry, GroupRelationship
    from flashsale.pay.models import SaleOrder

    order_ids = SaleOrder.objects.filter(sale_trade=sale_trade).values_list('oid', flat=True)
    week_start, week_end = week_range(sale_trade.pay_time)
    year_week = sale_trade.pay_time.strftime('%Y-%W')
    # 下属订单不计算到上级妈妈的订单销售
    order_carrys = OrderCarry.objects.filter(order_id__in=order_ids).exclude(carry_type=OrderCarry.REFERAL_ORDER)
    carry_first = order_carrys.first()
    if not (carry_first and carry_first.mama_id):
        return

    mama_id = carry_first.mama_id
    week_order_carrys = OrderCarry.objects.filter(
        date_field__range=(week_start, week_end), mama_id=mama_id,
        status__in=(OrderCarry.ESTIMATE, OrderCarry.CONFIRM))
    week_order_payment = sum(week_order_carrys.values_list('order_value', flat=True))
    base_missions = MamaMissionRecord.objects.filter(year_week=year_week, mama_id=mama_id)
    # update all mission's finish_value of the week range
    personal_records = base_missions.filter(
        mission__cat_type=MamaMission.CAT_SALE_MAMA
    )
    for record in personal_records:
        record.update_mission_value(week_order_payment)

    # 更新团队妈妈周销售任务
    mama_group = GroupRelationship.objects.filter(member_mama_id=mama_id).first()
    if mama_group:
        group_mission_record = MamaMissionRecord.objects.filter(
            year_week=year_week, mama_id=mama_group.leader_mama_id,
            mission__cat_type=MamaMission.CAT_SALE_GROUP
        ).first()

        if group_mission_record:
            group_mama_ids = GroupRelationship.objects.filter(leader_mama_id=mama_group.leader_mama_id)\
                .values_list('member_mama_id',flat=True)
            week_order_carrys = OrderCarry.objects.filter(
                date_field__range=(week_start, week_end), mama_id__in=group_mama_ids,
                status__in=(OrderCarry.ESTIMATE, OrderCarry.CONFIRM))
            week_group_payment = sum(week_order_carrys.values_list('order_value', flat=True))
            group_mission_record.update_mission_value(week_group_payment)

    from flashsale.xiaolumm.tasks import task_create_or_update_mama_mission_state
    task_create_or_update_mama_mission_state.delay(mama_id)



def order_payment_update_mission_record(sender, obj, *args, **kwargs):
    """ 订单支付成功更新妈妈销售激励状态 """
    try:
        logger.info('order_payment_update_mission_record start: tid= %s' % obj.tid)

        _update_mama_salepayment_mission_record(obj)

        logger.info('order_payment_update_mission_record end: tid= %s' % obj.tid)
    except Exception, exc:
        logger.error('order_payment_update_mission_record error: tid=%s, %s' % (obj.tid, exc), exc_info=True)


signal_saletrade_pay_confirm.connect(order_payment_update_mission_record,
                                           dispatch_uid='post_save_order_payment_update_mission_record')


def refund_confirm_update_mission_record(sender, obj, *args, **kwargs):
    """ 订单退款成功更新妈妈销售激励状态 """
    try:
        logger.info('refund_confirm_update_mission_record start: refund_id= %s' % obj.id)

        from flashsale.pay.models import SaleTrade
        sale_trade = SaleTrade.objects.get(id=obj.trade_id)

        _update_mama_salepayment_mission_record(sale_trade)

        logger.info('refund_confirm_update_mission_record end: refund_id= %s' % obj.id)
    except Exception, exc:
        logger.error('refund_confirm_update_mission_record error: refund_id=%s, %s' % (obj.id, exc), exc_info=True)

# 退款更新妈妈销售任务及团队销售任务
signal_saletrade_refund_confirm.connect(refund_confirm_update_mission_record,
                                           dispatch_uid='post_save_refund_confirm_update_mission_record')


# TODO@meron　团队妈妈邀请更新

