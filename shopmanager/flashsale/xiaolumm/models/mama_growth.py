# coding=utf-8
import datetime
from django.db import models
from django.db.models import Sum, Count

from core.models import BaseModel
from core.utils import week_range

import logging
logger = logging.getLogger(__name__)

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
        (CAT_TRIAL_MAMA, u'新增1元妈妈'),
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
    status = models.CharField(max_length=8, choices=STATUS_CHOICES,
                              default=DRAFT, verbose_name=u'状态')

    class Meta:
        db_table = 'flashsale_xlmm_mission'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈激励任务'
        verbose_name_plural = u'V2/妈妈激励任务列表'

    def is_receivable(self):
        """ 任务是否可以接收 """
        return self.status == MamaMission.PROGRESS


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

    finish_value = models.IntegerField(default=0, verbose_name=u'完成值')
    finish_time  = models.DateTimeField(blank=True, db_index=True, null=True, verbose_name=u'完成时间')

    uni_key  = models.CharField(max_length=32, unique=True, verbose_name=u'唯一约束') #mission_id + year_week + mama_id
    status = models.CharField(max_length=8, default=STAGING,choices=STATUS_CHOICES, db_index=True, verbose_name=u'状态')
    
    class Meta:
        db_table = 'flashsale_xlmm_missionrecord'
        index_together = [('mama_id', 'year_week', 'mission')]
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈激励任务记录'
        verbose_name_plural = u'V2/妈妈激励任务记录列表'

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

    def update_mission_value(self, finish_value):
        # TODO@meron 如果任务中订单金额退款，任务完成状态需要变更？
        self.finish_value = int(finish_value)
        cur_year_week = datetime.datetime.now().strftime('%Y-%W')
        if self.finish_value >= self.mission.target_value and self.is_staging():
            self.status = self.FINISHED
            self.finish_time = datetime.datetime.now()
        elif cur_year_week > self.year_week and self.is_staging():
            self.status = self.CLOSE
            self.finish_time = None
        self.save(update_fields=['finish_value', 'status', 'finish_time'])

        # TODO@meron 如果已通过添加佣金奖励记录


from flashsale.xiaolumm.signals import signal_xiaolumama_register_success
from flashsale.pay.signals import signal_saletrade_pay_confirm

def mama_register_update_mission_record(sender, xiaolumama, renew, *args, **kwargs):
    """ 妈妈注册成功更新推荐妈妈激励状态 """
    try:
        logger.debug('mama_register_update_mission_record start: mama=%s, renew=%s'%(xiaolumama, renew))
        from flashsale.xiaolumm.models import XiaoluMama, ReferalRelationship, PotentialMama
        parent_mama_ids = xiaolumama.get_parent_mama_ids()
        if not parent_mama_ids or renew:
            return
        parent_mama_id = parent_mama_ids[0]
        week_start, week_end = week_range(xiaolumama.charge_time.date())
        year_week = xiaolumama.charge_time.strftime('%Y-%W')
        if xiaolumama.last_renew_type == XiaoluMama.TRIAL:
            # 一元妈妈邀请数
            total_mama_count = PotentialMama.objects.filter(
                created__range=(week_start, week_end),
                referal_mama=parent_mama_id) \
                .aggregate(mama_count=Count('potential_mama')).get('mama_count')
            mission_record = MamaMissionRecord.objects.filter(
                mission__target=MamaMission.TARGET_PERSONAL,
                mission__cat_type= MamaMission.CAT_TRIAL_MAMA, # MamaMission.CAT_REFER_MAMA,
                year_week=year_week,
                mama_id=parent_mama_id
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
            mission_record = MamaMissionRecord.objects.filter(
                mission__target=MamaMission.TARGET_PERSONAL,
                mission__cat_type=MamaMission.CAT_REFER_MAMA,
                year_week=year_week,
                mama_id=parent_mama_id
            ).order_by('-status').first()
            if mission_record:
                mission_record.update_mission_value(total_mama_count)
        logger.debug('mama_register_update_mission_record end: %s' % xiaolumama)
    except Exception, exc:
        logger.error('mama_register_update_mission_record error: mama_id=%s, %s'%(xiaolumama.id ,exc), exc_info=True)

signal_xiaolumama_register_success.connect(mama_register_update_mission_record,
                                           dispatch_uid='post_save_mama_register_update_mission_record')


def order_payment_update_mission_record(sender, obj, *args, **kwargs):

    try:
        logger.debug('order_payment_update_mission_record start: saletrade= %s' % obj.tid)
        from flashsale.xiaolumm.models import XiaoluMama, OrderCarry
        from flashsale.pay.models import SaleOrder

        order_ids = SaleOrder.objects.filter(sale_trade=obj).values_list('oid', flat=True)

        week_start, week_end = week_range(obj.pay_time.date())
        year_week = obj.pay_time.strftime('%Y-%W')
        order_carrys = OrderCarry.objects.filter(order_id__in=order_ids)
        carry_first = order_carrys.first()
        if not (carry_first and carry_first.mama_id):
            return

        mama_id = carry_first.mama_id
        week_order_carrys = OrderCarry.objects.filter(
            date_field__range=(week_start, week_end), mama_id=mama_id,
            status__in=(OrderCarry.ESTIMATE, OrderCarry.CONFIRM))

        week_order_payment = sum(week_order_carrys.values_list('order_value', flat=True))
        # update all mission's finish_value of the week range
        mission_records = MamaMissionRecord.objects.filter(
            mission__target=MamaMission.TARGET_PERSONAL,
            mission__kpi_type=MamaMission.KPI_AMOUNT,
            year_week=year_week,
            mama_id=mama_id
        )
        for record in mission_records:
            record.update_mission_value(week_order_payment)

        logger.debug('order_payment_update_mission_record end: saletrade= %s' % obj.tid)
    except Exception, exc:
        logger.error('order_payment_update_mission_record error: tid=%s, %s' % (obj.tid, exc), exc_info=True)


signal_saletrade_pay_confirm.connect(order_payment_update_mission_record,
                                           dispatch_uid='post_save_order_payment_update_mission_record')


    
        
