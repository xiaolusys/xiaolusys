# coding=utf-8
import datetime
from django.db import models
from django.db.models import Sum, Count
from django.db.models.signals import post_save, pre_save

from core.models import BaseModel
from core.utils import week_range

from flashsale.xiaolumm import utils
from flashsale.xiaolumm import constants

import logging
logger = logging.getLogger(__name__)

def get_mama_week_sale_orders(mamaid_list, week_start, week_end):
    from flashsale.xiaolumm.models import OrderCarry
    order_carrys = OrderCarry.objects.filter(
        date_field__range=(week_start, week_end), mama_id__in=mamaid_list,
        status__in=(OrderCarry.ESTIMATE, OrderCarry.CONFIRM),
        carry_type__in=(OrderCarry.WAP_ORDER, OrderCarry.APP_ORDER)
    )
    return order_carrys

def get_mama_week_sale_amount(mamaid_list, week_start, week_end):
    carry_orders = get_mama_week_sale_orders(mamaid_list, week_start, week_end)
    return sum(carry_orders.values_list('order_value', flat=True))

def year_week_generator(end_year_week):
    cnt = 0
    while cnt < 100:
        yield end_year_week
        last_week = datetime.datetime.strptime('%s-0'%end_year_week, '%Y-%W-%w') - datetime.timedelta(days=7)
        end_year_week = last_week.strftime('%Y-%W')
        cnt += 1

def get_mama_week_finish_and_combo_list(mama_id, end_year_week):
    year_weeks = MamaMissionRecord.objects.filter(
        mama_id=mama_id,
        mission__cat_type=MamaMission.CAT_SALE_MAMA,
        status=MamaMissionRecord.FINISHED,
        year_week__lte=end_year_week
    ).order_by('year_week').values_list('year_week', flat=True)
    combo_week_list = []

    for year_week in year_week_generator(end_year_week):
        if year_week not in year_weeks:
            break
        combo_week_list.append(year_week)

    return year_weeks, combo_week_list

def year_week_range(year_week):
    dt = datetime.datetime.strptime('%s-0' % year_week, '%Y-%W-%w')
    return week_range(dt)


def get_mama_week_sale_mission(mama_id, year_week):
    mission = MamaMissionRecord.objects.filter(
        mama_id=mama_id,
        mission__cat_type=MamaMission.CAT_SALE_MAMA,
        year_week=year_week
    ).first()
    return mission


class MamaSaleGrade(BaseModel):

    A_LEVEL = 30000
    B_LEVEL = 60000
    C_LEVEL = 90000
    D_LEVEL = 120000
    E_LEVEL = 150000
    F_LEVEL = 180000
    G_LEVEL = 210000
    GRADE_CHOICES = (
        (A_LEVEL, u'A级: <300元'),
        (B_LEVEL, u'B级: <600元'),
        (C_LEVEL, u'C级: <900元'),
        (D_LEVEL, u'D级: <1200元'),
        (E_LEVEL, u'E级: <1500元'),
        (F_LEVEL, u'F级: <1800元'),
        (G_LEVEL, u'G级: <2100元'),
    )

    mama    = models.OneToOneField('xiaolumm.XiaoluMama',related_name='sale_grade',verbose_name=u'关联妈妈')

    grade   = models.IntegerField(default=0, choices=GRADE_CHOICES, db_index=True, verbose_name=u'销售级别')
    combo_count = models.IntegerField(default=0, db_index=True, verbose_name=u'连击次数')
    last_record_time = models.DateTimeField(null=True, blank=True, verbose_name=u'最后任务记录时间')

    total_finish_count = models.IntegerField(default=0, verbose_name=u'累计完成次数')
    first_finish_time = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name=u'最早完成时间')

    class Meta:
        db_table = 'flashsale_xlmm_salegrade'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈周销售业绩'
        verbose_name_plural = u'V2/妈妈周销售业绩列表'

    def __unicode__(self):
        return '<%s, %s>' % (self.mama, self.grade)

    @classmethod
    def create_or_update_mama_sale_grade(cls, xiaolumama):
        """
        1, 第一次创建，直接保存妈妈上周销售等级，及妈妈连续达标次数,记录日期, 总达标次数, 第一次达标时间;
        2, 如果记录日期非上周，则将上周任务等级更新成妈妈业绩等级,若升级连续达标次数不变，
            达标加1,未达清零,更新总达标次数，更新记录时间，第一次达标时间;
        """
        mama_id = xiaolumama.id
        sale_grade = cls.objects.filter(mama=xiaolumama).first()
        last_year_week = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%W')
        if not sale_grade:
            mama_last_mission = get_mama_week_sale_mission(mama_id, last_year_week)
            finish_week_list, combo_week_list = get_mama_week_finish_and_combo_list(mama_id, last_year_week)
            sale_grade = MamaSaleGrade(
                mama=xiaolumama,
                combo_count = 0,
                grade=cls.calc_sale_amount_grade(mama_last_mission and mama_last_mission.finish_value or 0),
                last_record_time= year_week_range(last_year_week)[1],
                total_finish_count= len(finish_week_list),
                first_finish_time= finish_week_list and year_week_range(finish_week_list[0])[1] or None
            )
            sale_grade.save()

        # 如果记录的日期不等于上周，则更新妈妈业绩记录
        record_year_week = sale_grade.last_record_time.strftime('%Y-%W')
        if record_year_week != last_year_week:
            mama_last_mission = get_mama_week_sale_mission(mama_id, last_year_week)
            finish_week_list, combo_week_list = get_mama_week_finish_and_combo_list(mama_id, last_year_week)
            last_week_grade = cls.calc_sale_amount_grade(mama_last_mission.finish_value)
            if sale_grade.grade > last_week_grade and not mama_last_mission.is_finished():
                sale_grade.combo_count = 0
            elif sale_grade.grade == last_week_grade and mama_last_mission.is_finished():
                sale_grade.combo_count += 1

            sale_grade.grade = last_week_grade
            # sale_grade.combo_count = len(combo_week_list)
            if not sale_grade.first_finish_time:
                sale_grade.first_finish_time = finish_week_list and finish_week_list[0] or None
            sale_grade.total_finish_count = len(finish_week_list)
            sale_grade.last_record_time = year_week_range(last_year_week)[1]
            sale_grade.save()

        return sale_grade


    @classmethod
    def calc_sale_amount_grade(cls, sale_amount):
        return min((int(sale_amount) / 30000  + 1)* 30000, cls.G_LEVEL)

    def get_week_target_amount_award(self, target_amount, year_week):
        """
        妈妈周激励奖励生成规则:
            1, 目标等级基础奖励 B: >300, >600, > 900 >1200 对应的最低奖励分别是: 15, 30, 45, 60;
            2, 连续达标奖励 S: 连续达标次数 * 15 (升级后连续达标次数除2取整)
            任务完成最终奖励: T = B + S
        """
        sale_grade = MamaSaleGrade.calc_sale_amount_grade(target_amount)
        base_award = utils.get_mama_sale_grade_award(sale_grade)
        if not self.last_record_time:
            return base_award

        next_record_week = (self.last_record_time + datetime.timedelta(days=7)).strftime('%Y-%W')
        if next_record_week == year_week:
            return base_award + utils.get_mama_sale_combo_award(self.combo_count)

        return base_award

    def get_week_target_amount(self, base_mission, year_week):
        """
        妈妈销售周激励目标生成规则：
            1, 若妈妈上周未完成目标，则上周目标继续,　若连续两周及以上未完成目标，则将目标下调一个等级;
            2, 如果上周任务完成或上周没有任务, 下周目标等级 = 完成值等级 + 1;
            3, 如果上周任务未完成， 下周目标等级 = max(上周目标等级 - 1 , 完成值等级 + 1, 1);
        """
        this_weekend = datetime.datetime.strptime('%s-0'%year_week, '%Y-%W-%w')
        last_weekend = (this_weekend - datetime.timedelta(days=7))
        week_start, week_end = week_range(last_weekend)
        mama_1st_record = MamaMissionRecord.objects.filter(
            mission=base_mission,
            year_week=last_weekend.strftime('%Y-%W'),
            mama_id=self.mama_id
        ).first()

        last_week_target_value = mama_1st_record and mama_1st_record.target_value or 0
        last_week_finish_value = get_mama_week_sale_amount([self.mama_id], week_start, week_end)
        finish_stage = utils.get_mama_target_stage(last_week_finish_value)
        last_target_stage = mama_1st_record and utils.get_mama_target_stage(last_week_target_value) or 0
        if mama_1st_record and mama_1st_record.is_finished():
            target_stage = max(finish_stage + 1, last_target_stage + 1)
        elif mama_1st_record and not mama_1st_record.is_finished():
            target_stage = max(last_target_stage - 1, finish_stage + 1, 1)
        else:
            target_stage = finish_stage + 1
        target_amount = utils.get_mama_stage_target(target_stage)
        return target_amount


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

    def is_receivable(self, mama_id):
        """
        妈妈周激励销售任务生成条件:
             1, 连续两周有订单;
        """
        if self.status != MamaMission.PROGRESS:
            return False

        if self.cat_type == self.CAT_SALE_MAMA:
            now_time_max = datetime.datetime.combine(datetime.datetime.today(), datetime.time.max)
            now_time_min = datetime.datetime.combine(datetime.datetime.today(), datetime.time.min)
            week_day     = int(now_time_max.strftime('%w')) or 7
            last_week_end = now_time_max - datetime.timedelta(days=week_day)
            two_week_ago = now_time_min - datetime.timedelta(days=week_day + 13)
            carry_orders = get_mama_week_sale_orders([mama_id], two_week_ago, last_week_end)
            carry_weeks  = set([dt.strftime('%Y-%W') for dt in carry_orders.values_list('date_field', flat=True)])
            return len(carry_weeks) > 1

        return True

    def get_mama_target_value(self, xiaolumama, day_datetime):
        """
        """
        from flashsale.xiaolumm.models import GroupRelationship, ReferalRelationship, XiaoluMama

        mama_id = xiaolumama.id
        # last_week_daytime = day_datetime - datetime.timedelta(days=7)
        # week_start , week_end = week_range(last_week_daytime)
        if self.kpi_type == self.KPI_AMOUNT and self.target == self.TARGET_PERSONAL:
            this_year_week = day_datetime.strftime('%Y-%W')
            sale_grade = MamaSaleGrade.create_or_update_mama_sale_grade(xiaolumama)
            target_amount = sale_grade.get_week_target_amount(self, this_year_week)
            award_amount  = sale_grade.get_week_target_amount_award(target_amount, this_year_week)
            return target_amount, award_amount

        elif self.kpi_type == self.KPI_AMOUNT:
            # group_mamas = GroupRelationship.objects.filter(leader_mama_id=xiaolumama.id)
            # mama_ids = list(group_mamas.values_list('member_mama_id', flat=True))
            # target_stages = constants.GROUP_TARGET_STAGE
            # award_rate = 50 * 100
            return self.target_value , self.award_amount

        if self.cat_type == MamaMission.CAT_REFER_MAMA:
            last_referal_num = ReferalRelationship.objects.filter(
                referal_from_mama_id=xiaolumama.id,
                status=ReferalRelationship.VALID,
                referal_type__in=(XiaoluMama.HALF, XiaoluMama.FULL)
            ).count()
            last_referal_num = max(last_referal_num, 1)
            return self.target_value, utils.get_award_carry_num(last_referal_num, XiaoluMama.FULL)

        return self.target_value, self.award_amount


def gen_mama_mission_record_unikey(mission_id, year_week, mama_id):
    return '%d-%s-%d'%(int(mission_id), year_week, int(mama_id))


class MamaMissionRecord(BaseModel):

    STAGING  = 'staging'
    FINISHED = 'finished'
    CLOSE    = 'close'
    CONFIRM  = 'confirm'
    CANCEL   = 'cancel'
    STATUS_CHOICES = (
        (STAGING, u'进行中'),
        (FINISHED, u'已完成'),
        (CLOSE, u'未完成')
    )

    UNI_NAME = 'weeklyaward'

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

    def is_close(self):
        return self.status == self.CLOSE

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
        return '{0}-{1}-{2}'.format(self.UNI_NAME ,self.mama_id, self.id)

    def update_mission_value(self, finish_value):
        cur_year_week = datetime.datetime.now().strftime('%Y-%W')
        # 任务奖励确认
        if finish_value >= self.target_value:
            if not self.is_finished():
                self.status = self.FINISHED
                self.finish_value = finish_value
                self.finish_time = datetime.datetime.now()
                self.save(update_fields=['finish_value', 'status', 'finish_time'])

                # 通知妈妈邀请任务奖励已发放, 该处值发放团队奖励, 妈妈销售奖励, 团队销售奖励
                if self.mission.kpi_type == MamaMission.KPI_AMOUNT:
                        # or self.mission.target == MamaMission.TARGET_GROUP:
                    from flashsale.xiaolumm.tasks import task_send_mama_weekly_award
                    task_send_mama_weekly_award.delay(self.mama_id, self.id)

        else:
            has_old_finished = self.is_finished()
            if has_old_finished:
                self.status = self.STAGING
                self.finish_value = finish_value
                self.finish_time = datetime.datetime.now()
                self.save(update_fields=['finish_value', 'status', 'finish_time'])

            if self.mission.kpi_type == MamaMission.KPI_AMOUNT \
                    or self.mission.target == MamaMission.TARGET_GROUP:
                from flashsale.xiaolumm.tasks import task_cancel_mama_weekly_award, \
                    task_push_mission_state_msg_to_weixin_user
                task_cancel_mama_weekly_award.delay(self.mama_id, self.id)

                # 通知妈妈奖励取消
                if has_old_finished:
                    task_push_mission_state_msg_to_weixin_user.delay(self.id, MamaMissionRecord.CANCEL)

        if cur_year_week > self.year_week and self.is_staging():
            self.status = self.CLOSE
            self.finish_value = finish_value
            self.save(update_fields=['finish_value', 'status'])

        if self.finish_value != finish_value:
            self.finish_value = finish_value
            self.save(update_fields=['finish_value'])

    @classmethod
    def mama_mission(cls, mama_id, year_week=None):
        queryset = cls.objects.filter(mama_id=mama_id)
        if year_week:
            queryset = queryset.filter(year_week=year_week)
        return queryset



from flashsale.xiaolumm.signals import signal_xiaolumama_register_success
from flashsale.pay.signals import signal_saletrade_pay_confirm, signal_saletrade_refund_confirm


def mama_register_update_mission_record(sender, xiaolumama, renew, *args, **kwargs):
    """ 妈妈注册成功更新推荐妈妈激励状态 """
    try:
        logger.info('mama_register_update_mission_record start: mama=%s, renew=%s'%(xiaolumama, renew))
        from flashsale.xiaolumm.models import XiaoluMama, ReferalRelationship, PotentialMama, GroupRelationship
        parent_mama_ids = xiaolumama.get_parent_mama_ids()
        if not parent_mama_ids:
            return

        parent_mama_id = parent_mama_ids[0]
        week_start, week_end = week_range(xiaolumama.charge_time)
        year_week = xiaolumama.charge_time.strftime('%Y-%W')

        base_missions = MamaMissionRecord.objects.filter(year_week=year_week, mama_id=parent_mama_id)
        if xiaolumama.last_renew_type == XiaoluMama.TRIAL:
            # 一元妈妈邀请数
            total_mama_count = PotentialMama.objects.filter(
                created__range=(week_start, week_end),
                referal_mama=parent_mama_id,
            ).aggregate(mama_count=Count('potential_mama')).get('mama_count')
            mission_record = base_missions.filter(
                mission__target=MamaMission.TARGET_PERSONAL,
                mission__cat_type= MamaMission.CAT_TRIAL_MAMA, # MamaMission.CAT_REFER_MAMA,
            ).order_by('-status').first()
            if mission_record:
                mission_record.update_mission_value(total_mama_count)

        else:
            # 正式妈妈邀请数
            total_mama_count = ReferalRelationship.objects.filter(
                modified__range=(week_start, week_end),
                status=ReferalRelationship.VALID,
                referal_from_mama_id=parent_mama_id,
                referal_type__in=XiaoluMama.REGULAR_MAMA_TYPES
            ).aggregate(mama_count=Count('referal_to_mama_id')).get('mama_count')
            mission_record = base_missions.filter(
                mission__target=MamaMission.TARGET_PERSONAL,
                mission__cat_type=MamaMission.CAT_REFER_MAMA,
            ).order_by('-status').first()
            if mission_record:
                mission_record.update_mission_value(total_mama_count)

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

    order_ids = list(SaleOrder.objects.filter(sale_trade=sale_trade).values_list('oid', flat=True))
    week_start, week_end = week_range(sale_trade.pay_time)
    year_week = sale_trade.pay_time.strftime('%Y-%W')
    # 下属订单不计算到上级妈妈的订单销售
    order_carrys = OrderCarry.objects.filter(order_id__in=order_ids).exclude(carry_type=OrderCarry.REFERAL_ORDER)
    carry_first = order_carrys.first()
    if not (carry_first and carry_first.mama_id):
        return

    mama_id = carry_first.mama_id
    week_order_payment = get_mama_week_sale_amount([mama_id], week_start, week_end)
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
            group_mama_ids = list(GroupRelationship.objects.filter(leader_mama_id=mama_group.leader_mama_id)\
                .values_list('member_mama_id',flat=True))
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

from .models_fortune import AwardCarry
def awardrecord_update_mission_record(sender, instance, *args, **kwargs):
    """ 订单退款成功更新妈妈销售激励状态 """
    try:
        logger.info('awardrecord_update_mission_record start: awardrecord= %s' % instance.id)

        if instance.carry_type == AwardCarry.AWARD_OPEN_COURSE and instance.date_field:
            year_week = instance.date_field.strftime('%Y-%W')
            mama_mission = MamaMissionRecord(
                mission__cat_type=MamaMission.CAT_OPEN_COURSE,
                mama_id=instance.mama_id,
                year_week=year_week
            ).first()

            if mama_mission:
                mama_mission.update_mission_value(1)

        logger.info('awardrecord_update_mission_record end: awardrecord= %s' % instance.id)
    except Exception, exc:
        logger.error('awardrecord_update_mission_record error: awardrecord=%s, %s' % (instance.id, exc), exc_info=True)

# 妈妈奖励列表更新更新妈妈任务状态
post_save.connect(awardrecord_update_mission_record,
                  sender=AwardCarry,
                  dispatch_uid='post_save_awardrecord_update_mission_record')

