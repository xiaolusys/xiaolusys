# coding=utf-8
from core.models import BaseModel
from django.db import models

from django.db.models.signals import post_save

import datetime


class MamaWeeklyAward(BaseModel):
    CAT_SALE_MAMA = 1
    CAT_SALE_GROUP = 2
    CAT_REFER_MAMA = 3
    CAT_GROUP_MAMA = 4
    CAT_FIRST_ORDER = 5
    CAT_OPEN_COURSE = 6
    CAT_FRESH_MAMA_TASK = 7
    CAT_TRIAL_MAMA = 8
    CAT_REFER_MAMA_TASK = 9
    
    CATEGORY_TYPES = ((CAT_SALE_MAMA, u'销售（个人）'), (CAT_SALE_GROUP, u'销售（团队）'), (CAT_REFER_MAMA, u'新增妈妈（下属）'),
                      (CAT_GROUP_MAMA, u'新增妈妈（团队）'),(CAT_FIRST_ORDER, u'首单奖励'), (CAT_OPEN_COURSE, u'授课奖金'),
                      (CAT_FRESH_MAMA_TASK, u'新手任务'), (CAT_TRIAL_MAMA, u'新增1元妈妈'), (CAT_REFER_MAMA_TASK, u'指导新手任务'))

    AWARD_SALE = 1
    AWARD_MEMBER = 2
    AWARD_TYPES = ((AWARD_SALE, u'销售奖金'), (AWARD_MEMBER, u'团队奖金'))

    WAIT_FINISH = 1
    ALREADY_FINISH = 2
    NOT_FINISH = 3
    FINISH_STATUS = ((WAIT_FINISH, u'待完成'), (ALREADY_FINISH, u'已完成'), (NOT_FINISH, u'未完成'))

    STATUS_TYPES = ((1, 'Valid'), (2, 'Invalid'))
    
    mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'妈妈id')
    referal_from_mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'推荐人id')
    group_leader_mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'团队队长id')
    week_field = models.CharField(max_length=32, blank=True, unique=True, verbose_name=u'week_id') #2016-32
    target_num = models.IntegerField(default=0, verbose_name=u'目标数')
    finish_num = models.IntegerField(default=0, verbose_name=u'完成数')
    award_num = models.IntegerField(default=0, verbose_name=u'奖金')
    category_type = models.IntegerField(default=0, choices=CATEGORY_TYPES, db_index=True, verbose_name=u'奖励项目')
    award_type ＝ models.IntegerField(default=0, choices=AWARD_TYPES, db_index=True, verbose_name=u'奖励类型')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID') #mama_id + week_field + category_type
    finish_status = models.IntegerField(default=0, choices=FINISH_STATUS, db_index=True, verbose_name=u'完成状态')
    status = models.IntegerField(default=0, choices=STATUS_TYPES, db_index=True, verbose_name=u'状态')
    
    class Meta:
        db_table = 'flashsale_xlmm_mamaweeklyaward'
        app_label = 'xiaolumm'
        verbose_name = u'V2/妈妈weekly奖金'
        verbose_name_plural = u'V2/妈妈weekly奖金列表'

    @staticmethod
    def gen_week_field(self, date_time):
        ic = date_time.isocalendar()
        return "%s-week-%s" % (ic[0], ic[1])

    @staticmethod
    def gen_unikey(self, mama_id, week_field, category_type):
        return "%s|%s|%s" % (mama_id, week_field, category_type)

    
        
