# coding=utf-8
from core.models import BaseModel
from django.db import models

from django.db.models.signals import post_save

import datetime

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

    TYPE_WEEKLY = 'weekly'
    TYPE_DEADLINE = 'deadline'
    TYPE_MOUNTHLY = 'monthly'
    TYPE_CHOICES = (
        (TYPE_WEEKLY, u'周任务'),
        (TYPE_MOUNTHLY, u'月任务'),
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

    CAT_SALE_MAMA = 1
    CAT_SALE_GROUP = 2
    CAT_REFER_MAMA = 3
    CAT_GROUP_MAMA = 4
    CAT_FIRST_ORDER = 5
    CAT_OPEN_COURSE = 6
    CAT_FRESH_MAMA_TASK = 7
    CAT_TRIAL_MAMA = 8
    CAT_REFER_MAMA_TASK = 9

    CATEGORY_TYPES = ((CAT_SALE_MAMA, u'销售（个人）'), (CAT_SALE_GROUP, u'销售（团队）'),
                      (CAT_REFER_MAMA, u'新增妈妈（下属）'), (CAT_GROUP_MAMA, u'新增妈妈（团队）'),
                      (CAT_FIRST_ORDER, u'首单奖励'), (CAT_OPEN_COURSE, u'授课奖金'),
                      (CAT_FRESH_MAMA_TASK, u'新手任务'), (CAT_TRIAL_MAMA, u'新增1元妈妈'),
                      (CAT_REFER_MAMA_TASK, u'指导新手任务'))

    name   = models.CharField(max_length=64, verbose_name=u'任务名称')
    target = models.CharField(max_length=8, default=TARGET_PERSONAL,
                              choices=TARGET_CHOICES, verbose_name=u'任务对象')
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

    # 　TODO 销售任务需要根据订单完成功才能奖励

    class Meta:
        db_table = 'flashsale_xlmm_mission'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈激励任务'
        verbose_name_plural = u'V2/妈妈激励任务列表'

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

    
        
