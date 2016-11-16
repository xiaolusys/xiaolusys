# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import datetime
from django.db import models
from django.db.models import Sum, F, Count, Q
from django.db import connection, transaction
from django.db.models.signals import post_save
from core.models import BaseModel, AdminModel
from core.fields import JSONCharMyField
from flashsale.xiaolumm.models import XiaoluMama, MamaFortune, CashOut
from flashsale.xiaolumm.models.models_fortune import CarryRecord, OrderCarry, AwardCarry, ClickCarry, \
    MAMA_FORTUNE_HISTORY_LAST_DAY
from django.core.cache import cache
import logging
from copy import copy

logger = logging.getLogger('django.request')


# 在下次活动前设置此处，以自动重设变更统计时间
STAT_TIME = datetime.datetime(2016, 8, 26)
STAT_END_TIME = datetime.datetime(2016, 9, 10)
# ----------------------------------------------------------------
#    MamaCarryTotal 与 MamaTeamCarryTotal 及Record后续弃用
# ----------------------------------------------------------------


# if datetime.datetime.now() < datetime.datetime(2016, 7, 28) \
# else datetime.datetime(2016, 7, 28)
class RankRedis(object):
    @staticmethod
    def redis_cache():
        if not hasattr(RankRedis, '__redis_cache__'):
            RankRedis.__redis_cache__ = cache.get_master_client()
        return RankRedis.__redis_cache__

    def __init__(self, stat_time):
        self.stat_time = stat_time

    def get_cache_key(self, model_class, target='total'):
        if model_class.__name__ in ['WeekMamaCarryTotal', 'WeekMamaTeamCarryTotal']:
            return model_class.__name__ + '.' + self.stat_time.strftime('%Y%m%d') + '.' + target
        if model_class.__name__ in ['ActivityMamaCarryTotal', 'ActivityMamaTeamCarryTotal']:
            return model_class.__name__ + '.activity.' + target
        raise Exception(u'unexpected model class ')

    def update_cache(self, instance, targets=['duration_total', 'total'], func=getattr):
        for target in targets:
            RankRedis.redis_cache().zadd(self.get_cache_key(type(instance), target), instance.mama_id,
                                       func(instance, target))

    def batch_update_cache(self, res, modelclass, target='total'):
        RankRedis.redis_cache().zadd(self.get_cache_key(modelclass, target), **res)

    def clear_cache(self, model_class, target):
        RankRedis.redis_cache().delete(self.get_cache_key(model_class, target))

    def get_rank_count(self, model_class, target):
        return RankRedis.redis_cache().zcard(self.get_cache_key(model_class, target))

    def get_rank_list(self, model_class, target, start, stop):
        return RankRedis.redis_cache().zrevrange(self.get_cache_key(model_class, target), start, stop)

    def get_rank_dict(self, model_class, target, start, stop):
        return dict(zip(RankRedis.redis_cache().zrevrange(self.get_cache_key(model_class, target), start, stop),
                        range(start + 1, stop + 1)))

    def get_rank(self, model_class, target, mama_id):
        rank = RankRedis.redis_cache().zrevrank(self.get_cache_key(model_class, target), mama_id) or 0
        return rank + 1

    def is_locked(self, lock_key):
        return bool(RankRedis.redis_cache().get(lock_key))

    def lock(self, lock_key):
        return RankRedis.redis_cache().set(lock_key, 1, 5)


def get_stat_rank_redis():
    return RankRedis(STAT_TIME)


STAT_RANK_REDIS = get_stat_rank_redis()


class BaseMamaCarryTotal(BaseModel):
    last_renew_type = models.IntegerField(choices=XiaoluMama.RENEW_TYPE, default=365, db_index=True,
                                          verbose_name=u"最近续费类型")
    agencylevel = models.IntegerField(default=XiaoluMama.INNER_LEVEL, db_index=True, choices=XiaoluMama.AGENCY_LEVEL,
                                      verbose_name=u"代理类别")

    class Meta:
        abstract = True

    @property
    def mama_nick(self):
        return self.mama.get_customer().nick

    @property
    def thumbnail(self):
        return self.mama.get_customer().thumbnail

    @property
    def mobile(self):
        return self.mama.get_customer().mobile

    @property
    def phone(self):
        return self.mama.get_customer().phone


class MamaCarryTotal(BaseMamaCarryTotal):
    """
        准备删除
    """
    mama = models.OneToOneField(XiaoluMama, primary_key=True)
    stat_time = models.DateTimeField(default=STAT_TIME, db_index=True, verbose_name=u'统计起始时间')
    history_total = models.IntegerField(default=0, verbose_name=u'历史收益总额', help_text=u'单位为分')
    history_confirm = models.BooleanField(default=False, verbose_name=u'历史收益确认', help_text=u'单位为分')
    duration_total = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    expect_total = models.IntegerField(default=0, verbose_name=u'统计期间预期收益总额', help_text=u'单位为分，不包含duration_total')
    history_num = models.IntegerField(default=0, db_index=True, verbose_name=u'历史订单数量')
    duration_num = models.IntegerField(default=0, verbose_name=u'活动订单数量')
    expect_num = models.IntegerField(default=0, verbose_name=u'统计期间预期订单数量')
    total_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'总排名',
                                           help_text=u'单位为分,每日更新，从cache中可实时更新')
    duration_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'活动期排名',
                                              help_text=u'单位为分，每日更新，从cache中可实时更新')
    de_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'活动期预期排名',
                                        help_text=u'单位为分，每日更新，从cache中可实时更新,包含duration_total')
    activite_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'特定活动排名',
                                              help_text=u'单位为分，每日更新，从cache中可实时更新,包含duration_total')

    carry_records = JSONCharMyField(max_length=10240, blank=True, default='[]', verbose_name=u'每日收益关联',
                                    help_text=u"好像没啥用准备删掉了")

    # invitate_num = 邀请数
    # activite_num 激活数
    class Meta:
        db_table = 'xiaolumm_carry_total'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈收益排名'
        verbose_name_plural = u'小鹿妈妈收益排名列表'

    @property
    def num(self):
        return self.history_num + self.duration_num

    @property
    def total(self):
        return self.history_total + self.duration_total

    @property
    def rank(self):
        if not hasattr(self, '_rank_'):
            return 0
        return self._rank_

    @property
    def total_rank(self):
        return self.total_rank_delay if self.total_rank_delay else 0

    @property
    def duration_rank(self):
        return self.duration_rank_delay if self.duration_rank_delay else 0

    @property
    def de_rank(self):
        return self.de_rank_delay if self.de_rank_delay else 0

    @property
    def activite_rank(self):
        return self.activite_rank_delay if self.activite_rank_delay else 0

    @property
    def total_display(self):
        return float('%.2f' % (self.total * 0.01))

    @property
    def duration_total_display(self):
        return '%.2f' % (self.duration_total * 0.01)

    def __unicode__(self):
        return 'mama rank:%d' % (self.mama_id,) if self.mama_id else 'mama rank init'

    @staticmethod
    def generate(mama):
        if type(mama) != XiaoluMama:
            mama = XiaoluMama.objects.get(id=mama)
        mama_id = mama.id
        rank = MamaCarryTotal(mama_id=mama_id, last_renew_type=mama.last_renew_type, agencylevel=mama.agencylevel)
        rank.set_data()
        rank.save()
        return rank

    @staticmethod
    def update_or_create(mama_id):
        if not MamaCarryTotal.objects.filter(mama_id=mama_id).exists():
            return MamaCarryTotal.generate(mama_id)
        rank = MamaCarryTotal.objects.filter(mama_id=mama_id).first()
        rank.set_data()
        rank.save()
        return rank

    def set_data(self, query_history=True):
        mama_id = self.mama_id
        if query_history:
            self.set_history_data()
        sum_res = CarryRecord.objects.filter(date_field__gte=STAT_TIME, date_field__lt=STAT_END_TIME, mama_id=mama_id).exclude(
            status=CarryRecord.CANCEL). \
            values('status').annotate(total=Sum('carry_num'))
        sum_dict = {entry["status"]: entry["total"] for entry in sum_res}
        self.duration_total = sum_dict.get(CarryRecord.CONFIRMED, 0)
        self.expect_total = sum_dict.get(CarryRecord.PENDING, 0)
        if self.duration_total + self.expect_total:
            records = CarryRecord.objects.filter(date_field__gte=STAT_TIME, date_field__lt=STAT_END_TIME, mama_id=mama_id,
                                                 status__in=[CarryRecord.PENDING, CarryRecord.CONFIRMED])
            self.carry_records = [c.id for c in records]
            sum_res = OrderCarry.objects.filter(mama_id=mama_id, status__in=[1, 2], created__gte=STAT_TIME, created__lt=STAT_END_TIME). \
                values('status').annotate(total=Count('id'))
            expect_num = 0
            duration_num = 0
            for entry in sum_res:
                if entry["status"] == 1:
                    expect_num = entry.get("total") or 0
                elif entry["status"] == 2:
                    duration_num = entry["total"]
            self.expect_num = expect_num
            self.duration_num = duration_num

    def set_history_data(self):
        mama_id = self.mama_id
        self.history_total = self.get_history_total()
        self.history_num = OrderCarry.objects.filter(mama_id=mama_id, status=2, created__lt=STAT_TIME).count()
        self.history_confirm = CarryRecord.objects.filter(date_field__gt=MAMA_FORTUNE_HISTORY_LAST_DAY,
                                                          date_field__lte=STAT_TIME, mama_id=mama_id,
                                                          status=CarryRecord.PENDING).exists()

    @staticmethod
    @transaction.atomic
    def get_by_mama_id(mama_id):
        if not MamaCarryTotal.objects.filter(mama_id=mama_id).exists():
            return MamaCarryTotal.generate(mama_id)
        return MamaCarryTotal.objects.get(mama_id=mama_id)

    def get_history_total(self):
        cr_history = CarryRecord.objects.filter(mama_id=self.mama_id, date_field__gt=MAMA_FORTUNE_HISTORY_LAST_DAY,
                                                date_field__lt=STAT_TIME, status__in=[1, 2]).aggregate(
            carry=Sum('carry_num')).get('carry') or 0
        fortune = MamaFortune.objects.filter(mama_id=self.mama_id).first()
        history_confirmed = fortune.history_confirmed if fortune else 0
        history_cash_out = fortune.history_cashout
        return cr_history + history_confirmed + history_cash_out

    @staticmethod
    def move_other_stat_to_record():
        moves = []
        dels = []
        for i in MamaCarryTotal.objects.exclude(stat_time=STAT_TIME):
            c = CarryTotalRecord.create(i, save=False)
            dels.append(i.mama_id)
            moves.append(c)
        CarryTotalRecord.objects.bulk_create(moves)
        MamaCarryTotal.objects.filter(mama_id__in=dels).delete()

    @staticmethod
    def batch_generate():
        """
            生成新排名榜
            1/移除非统计时间的统计
            2/对不存在该统计时间的mamaid，生成新排名记录
        """
        MamaCarryTotal.move_other_stat_to_record()
        mama_data = {i['id']: i
                     for i in XiaoluMama.objects.filter(progress__in=[XiaoluMama.PAY, XiaoluMama.PASS],
                                                        status__in=[XiaoluMama.EFFECT, XiaoluMama.FROZEN],
                                                        charge_status=XiaoluMama.CHARGED).values(
            'id', 'last_renew_type', 'agencylevel')}
        mama_ids = mama_data.keys()
        exist_ids = [m['mama_id'] for m in MamaCarryTotal.objects.filter(stat_time=STAT_TIME).values('mama_id')]

        mama_ids = list(set(mama_ids) - set(exist_ids))
        # res = []
        for mama_id in mama_ids:
            m = MamaCarryTotal(mama_id=mama_id, last_renew_type=mama_data[mama_id].get('last_renew_type', 365),
                               agencylevel=mama_data[mama_id].get('agencylevel', 1))
            m.set_data()
            m.save()

    @staticmethod
    def stat_history_total(mama_id):
        """
            历史总金额为OrderCarry,AwardCarry,ClickCarry
        """
        if not MamaCarryTotal.objects.filter(mama_id=mama_id).exists():
            return MamaCarryTotal.generate(mama_id)
        rank = MamaCarryTotal.objects.get(mama_id=mama_id)
        rank.set_history_data()
        rank.save(update_fields=['history_total', 'history_num', 'history_confirm', 'modified'])

    @staticmethod
    def stat_batch_history_total():
        mids = [m['mama_id'] for m in MamaCarryTotal.objects.values('mama_id')]
        for mmid in mids:
            MamaCarryTotal.stat_history_total(mmid)

    @staticmethod
    def update_ranking(mama_id, must_query_history=False):
        """
            更新数据以更新排名-其实这个方法尽可能更新了需要的数，唯独不更新排名
            排名更新在post_save事件中，15分钟以后，由celery事件更新排名。
        """
        if not MamaCarryTotal.objects.filter(mama_id=mama_id).exists():
            return MamaCarryTotal.generate(mama_id)
        rank = MamaCarryTotal.objects.get(mama_id=mama_id)
        rank.set_data(query_history=must_query_history or not rank.history_confirm)
        rank.save()
        return rank

    ############################## VIEW API ############################
    @staticmethod
    def get_ranking_list():
        return MamaCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL).order_by(
            (F('duration_total') + F('history_total')).desc())

    @staticmethod
    def get_duration_ranking_list():
        return MamaCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL).order_by(
            (F('duration_total')).desc())

    @staticmethod
    def get_activity_ranking_list():
        """
            一元开店，取一元妈妈活动总收益（预期收益+确定收益）排名
        """
        return MamaCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL,
                                             last_renew_type=XiaoluMama.TRIAL).order_by(
            (F('duration_total') + F('expect_total')).desc())

    ############################## TASK API ############################
    @staticmethod
    def reset_rank():
        MamaCarryTotal.batch_generate()
        i = 1
        rank = 1
        last_value = None
        res = {}
        for m in MamaCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL).order_by(
                (F('duration_total') + F('history_total')
                 ).desc()).values('mama_id',
                                  'duration_total',
                                  'history_total'):
            if last_value is None or m['duration_total'] + m['history_total'] < last_value:
                last_value = m['duration_total'] + m['history_total']
                rank = i
            res[m['mama_id']] = rank
            i += 1
        multi_update(MamaCarryTotal, 'mama_id', 'total_rank_delay', res)

    @staticmethod
    def reset_rank_duration():
        MamaCarryTotal.batch_generate()
        i = 1
        rank = 1
        last_value = None
        res = {}
        for m in MamaCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL).order_by(
                (F('duration_total')).desc()).values('mama_id', 'duration_total'):
            if last_value is None or m['duration_total'] < last_value:
                last_value = m['duration_total']
                rank = i
            res[m['mama_id']] = rank
            i += 1
        multi_update(MamaCarryTotal, 'mama_id', 'duration_rank_delay', res)

    @staticmethod
    def reset_de_rank():
        MamaCarryTotal.batch_generate()
        i = 1
        rank = 1
        last_value = None
        res = {}
        for m in MamaCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL).order_by(
                (F('duration_total') + F('expect_total')
                 ).desc()).values('mama_id', 'duration_total', 'expect_total'):
            if last_value is None or m['duration_total'] + m['expect_total'] < last_value:
                last_value = m['duration_total'] + m['expect_total']
                rank = i
            res[m['mama_id']] = rank
            i += 1
        multi_update(MamaCarryTotal, 'mama_id', 'de_rank_delay', res)

    @staticmethod
    def reset_activite_rank():
        MamaCarryTotal.batch_generate()
        i = 1
        rank = 1
        last_value = None
        res = {}
        for m in MamaCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL,
                                               last_renew_type=XiaoluMama.TRIAL).exclude(
            agencylevel=XiaoluMama.INNER_LEVEL).order_by(
            (F('duration_total') + F('expect_total')).desc()).values('mama_id', 'duration_total', 'expect_total'):
            if last_value is None or m['duration_total'] + m['expect_total'] < last_value:
                last_value = m['duration_total'] + m['expect_total']
                rank = i
            res[m['mama_id']] = rank if last_value > 0 else 0
            i += 1
        if res:
            multi_update(MamaCarryTotal, 'mama_id', 'activite_rank_delay', res)


# 至多一次更新2000W,更多要更新数据库架构啦
def multi_update(model_class, key_attr, value_attr, res, where=''):
    if not res:
        raise Exception('set values res empty')
    sql_begin = 'UPDATE %s SET %s = CASE %s ' % (model_class._meta.db_table, value_attr, key_attr)
    sql_when_str = lambda key: 'WHEN %s THEN %s' % (key, res[key])
    sql_whens_list = []
    SLICE_LEN = 20000
    res_keys = res.keys()
    for i in range(0, 1000):
        slice = res_keys[i * SLICE_LEN: i * SLICE_LEN + SLICE_LEN]
        sql_whens_list.append(slice)
    for item in sql_whens_list:
        if item:
            sql_end = ' END where %s in (%s)' % (key_attr, ','.join([str(i) for i in item]))
            if where:
                sql_end = sql_end + ' AND ' + where
            sql = sql_begin + ' '.join([sql_when_str(key) for key in item]) + sql_end
            cursor = connection.cursor()
            cursor.execute(sql)
            cursor.close()


class BaseMamaTeamCarryTotal(BaseMamaCarryTotal):
    class Meta:
        abstract = True

    @property
    def mama_ids(self):
        if not hasattr(self, '_mama_ids'):
            # self._mama_ids_ = MamaTeamCarryTotal.get_team_ids(self.mama_id)
            self._mama_ids_ = [m['mama_id'] for m in self.members.values('mama_id')]
        return self._mama_ids_

    @property
    def total_display(self):
        return float('%.2f' % (self.total * 0.01))

    @property
    def duration_total_display(self):
        return float('%.2f' % (self.duration_total * 0.01))

    @staticmethod
    def get_team_ids(mama_id):
        mama = XiaoluMama.objects.get(id=mama_id)
        return mama.get_team_member_ids()


class MamaTeamCarryTotal(BaseMamaTeamCarryTotal):
    """
        准备删除
    """
    mama = models.OneToOneField(XiaoluMama, primary_key=True)
    members = models.ManyToManyField(MamaCarryTotal, related_name='teams')
    total = models.IntegerField(default=0, verbose_name=u'团队收益总额', help_text=u'单位为分')
    num = models.IntegerField(default=0, verbose_name=u'团队订单数量')
    duration_num = models.IntegerField(default=0, verbose_name=u'活动期间团队订单数量')
    expect_num = models.IntegerField(default=0, verbose_name=u'统计期间预期订单数量', help_text=u"包含了duration_num")
    duration_total = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    expect_total = models.IntegerField(default=0, verbose_name=u'统计期间预期收益总额', help_text=u'单位为分，包含了duration_total')
    stat_time = models.DateTimeField(default=STAT_TIME, db_index=True, verbose_name=u'统计起始时间')
    total_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'总排名',
                                           help_text=u'单位为分,每日更新，从cache中可实时更新')
    duration_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'活动期排名',
                                              help_text=u'单位为分，每日更新，从cache中可实时更新')
    de_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'活动期预期排名',
                                        help_text=u'单位为分，每日更新，从cache中可实时更新')
    activite_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'特定活动排名',
                                              help_text=u'单位为分，每日更新，从cache中可实时更新,包含duration_total')

    class Meta:
        db_table = 'xiaolumm_team_carry_total'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈团队收益排名'
        verbose_name_plural = u'小鹿妈妈团队收益排名列表'

    def __unicode__(self):
        return 'mama rank:%d' % (self.mama_id,)

    @property
    def rank(self):
        if not hasattr(self, '_rank_'):
            return 0
        return self._rank_

    @property
    def total_rank(self):
        return self.total_rank_delay if self.total_rank_delay else 0

    @property
    def duration_rank(self):
        return self.duration_rank_delay if self.duration_rank_delay else 0

    @property
    def de_rank(self):
        return self.de_rank_delay if self.de_rank_delay else 0

    @property
    def activite_rank(self):
        return self.activite_rank_delay if self.activite_rank_delay else 0

    @staticmethod
    def move_other_stat_to_record():
        moves = []
        dels = []
        for i in MamaTeamCarryTotal.objects.exclude(stat_time=STAT_TIME).prefetch_related('members'):
            c = TeamCarryTotalRecord.create(i, save=False)
            dels.append(i.mama_id)
            moves.append(c)
        TeamCarryTotalRecord.objects.bulk_create(moves)
        MamaTeamCarryTotal.objects.filter(mama_id__in=dels).delete()

    @staticmethod
    def batch_generate():
        MamaTeamCarryTotal.move_other_stat_to_record()
        MamaCarryTotal.batch_generate()
        mids = [m['mama_id'] for m in MamaCarryTotal.objects.values('mama_id')]
        tmids = [m['mama_id'] for m in MamaTeamCarryTotal.objects.values('mama_id')]
        left_ids = list(set(mids) - set(tmids))
        for mama_id in left_ids:
            MamaTeamCarryTotal.generate(mama_id)

    @staticmethod
    def update_or_create(mama_id):
        if not MamaTeamCarryTotal.objects.filter(mama_id=mama_id).exists():
            return MamaTeamCarryTotal.generate(mama_id)
        m = MamaTeamCarryTotal.objects.filter(mama_id=mama_id).first()
        mama_ids = MamaTeamCarryTotal.get_team_ids(mama_id)
        m.restat(mama_ids)
        m.save()
        now_mama_ids = [i['mama_id'] for i in m.members.values('mama_id')]
        left_mama_ids = list(set(mama_ids) - set(now_mama_ids))
        for mama in MamaCarryTotal.objects.filter(mama_id__in=left_mama_ids):
            m.members.add(mama)
        m.save()
        return

    @staticmethod
    def generate(mama):
        if type(mama) != XiaoluMama:
            mama = XiaoluMama.objects.get(id=mama)
        mama_id = mama.id
        mama_ids = mama.get_team_member_ids()
        m = MamaTeamCarryTotal(
            mama_id=mama_id,
            last_renew_type=mama.last_renew_type,
            agencylevel=mama.agencylevel
        )
        m.restat(mama_ids)
        m.save()
        for mama in MamaCarryTotal.objects.filter(mama_id__in=mama_ids):
            m.members.add(mama)
        m.save()
        return m

    def restat(self, mama_ids):
        res = MamaCarryTotal.objects.filter(mama_id__in=mama_ids).aggregate(
            total=Sum('history_total') + Sum('duration_total'),
            duration_total=Sum('duration_total'),
            expect_total=Sum('duration_total') + Sum('expect_total'),
            num=Sum('history_num') + Sum('duration_num'),
            duration_num=Sum('duration_num'),
            expect_num=Sum('expect_num') + Sum('duration_num'),
        )
        self.total = res.get('total') or 0
        self.duration_total = res.get('duration_total') or 0
        self.expect_total = res.get('expect_total') or 0
        self.num = res.get('num') or 0
        self.duration_num = res.get('duration_num') or 0
        self.expect_num = res.get('expect_num') or 0

    def refresh_data(self):
        self.restat(self.mama_ids)
        self.save()

    @staticmethod
    def update_by_mama_id(mama):
        """
            一个妈妈改变，引起相关妈妈团队都变化
        """
        for team in mama.teams.all():
            team.refresh_data()

    @classmethod
    @transaction.atomic
    def get_by_mama_id(cls, mama_id):
        if not cls.objects.filter(mama_id=mama_id).exists():
            return cls.generate(mama_id)
        return cls.objects.filter(mama_id=mama_id).first()

    @staticmethod
    def get_ranking_list():
        return MamaTeamCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL).order_by((F('total')).desc())

    @staticmethod
    def get_duration_ranking_list():
        return MamaTeamCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL).order_by(
            (F('duration_total')).desc())

    @staticmethod
    def get_activity_ranking_list():
        return MamaTeamCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL).order_by(
            (F('expect_total')).desc())

    @staticmethod
    def reset_rank():
        MamaTeamCarryTotal.batch_generate()
        i = 1
        rank = 1
        last_value = None
        res = {}
        for m in MamaTeamCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL).order_by(
                (F('total')).desc()).values('mama_id', 'total'):
            if last_value is None or m['total'] < last_value:
                last_value = m['total']
                rank = i
            res[m['mama_id']] = rank
            i += 1
        multi_update(MamaTeamCarryTotal, 'mama_id', 'total_rank_delay', res)

    @staticmethod
    def reset_rank_duration():
        MamaTeamCarryTotal.batch_generate()
        i = 1
        rank = 1
        last_value = None
        res = {}
        for m in MamaTeamCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL).order_by(
                (F('duration_total')).desc()).values('mama_id', 'duration_total'):
            if last_value is None or m['duration_total'] < last_value:
                last_value = m['duration_total']
                rank = i
            res[m['mama_id']] = rank
            i += 1
        multi_update(MamaTeamCarryTotal, 'mama_id', 'duration_rank_delay', res)

    @staticmethod
    def reset_de_rank():
        MamaTeamCarryTotal.batch_generate()
        i = 1
        rank = 1
        last_value = None
        res = {}
        for m in MamaTeamCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL).order_by((F('expect_total')
                                                                                                     ).desc()).values(
            'mama_id', 'expect_total'):
            if last_value is None or m['expect_total'] < last_value:
                last_value = m['expect_total']
                rank = i
            res[m['mama_id']] = rank
            i += 1
        multi_update(MamaTeamCarryTotal, 'mama_id', 'de_rank_delay', res)

    @staticmethod
    def reset_activite_rank():
        MamaTeamCarryTotal.batch_generate()
        i = 1
        rank = 1
        last_value = None
        res = {}
        for m in MamaTeamCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL).order_by(
                (F('expect_total')).desc()).values('mama_id', 'expect_total'):
            if last_value is None or m['expect_total'] < last_value:
                last_value = m['expect_total']
                rank = i
            res[m['mama_id']] = rank
            i += 1
        if res:
            multi_update(MamaTeamCarryTotal, 'mama_id', 'activite_rank_delay', res)


class CarryTotalRecord(BaseModel):
    """
        活动记录
    """
    mama = models.ForeignKey(XiaoluMama)
    last_renew_type = models.IntegerField(choices=XiaoluMama.RENEW_TYPE, default=365, db_index=True,
                                          verbose_name=u"最近续费类型")
    agencylevel = models.IntegerField(default=XiaoluMama.INNER_LEVEL, db_index=True, choices=XiaoluMama.AGENCY_LEVEL,
                                      verbose_name=u"代理类别")
    stat_time = models.DateTimeField(verbose_name=u'统计时间', db_index=True)
    total_rank = models.IntegerField(default=0, verbose_name=u'总额排名')
    duration_rank = models.IntegerField(default=0, verbose_name=u'活动期间排名')
    history_total = models.IntegerField(default=0, verbose_name=u'历史收益总额', help_text=u'单位为分')
    duration_total = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    expect_total = models.IntegerField(default=0, verbose_name=u'统计期间预期收益总额', help_text=u'单位为分，不包含duration_total')
    history_num = models.IntegerField(default=0, db_index=True, verbose_name=u'团队订单数量')
    duration_num = models.IntegerField(default=0, verbose_name=u'活动期间团队订单数量')
    expect_num = models.IntegerField(default=0, verbose_name=u'统计期间预期订单数量')
    carry_records = JSONCharMyField(max_length=10240, blank=True, default='[]', verbose_name=u'每日收益关联')
    record_time = models.DateTimeField(null=True, db_index=True, verbose_name=u'记录批次时间')
    type = models.IntegerField(default=0, db_index=True, choices=((0, u'默认'), (1, u'活动统计'), (2, u'每周统计')))

    class Meta:
        db_table = 'xiaolumm_carry_total_record'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈收益排名记录'
        verbose_name_plural = u'小鹿妈妈收益排名记录'

    @staticmethod
    def create(carry_total, save=True, record_time=None, type=0):
        record = CarryTotalRecord(
            mama_id=carry_total.mama_id,
            last_renew_type=carry_total.last_renew_type,
            agencylevel=carry_total.agencylevel,
            stat_time=carry_total.stat_time,
            total_rank=carry_total.total_rank,
            duration_rank=carry_total.duration_rank,
            history_total=carry_total.history_total,
            duration_total=carry_total.duration_total,
            history_num=carry_total.history_num,
            duration_num=carry_total.duration_num,
            carry_records=carry_total.carry_records,
            record_time=datetime.datetime.now() if record_time is None else record_time,
            type=type
        )
        if save:
            record.save()
        return record

    @staticmethod
    def snapshot(stat_time):
        rank = 1
        for m in MamaCarryTotal.get_ranking_list()[0:500]:
            CarryTotalRecord(
                stat_time=stat_time,
                mama=m,
                total_rank=rank,
                history_total=m.history_total,
                duration_total=m.duration_total,
                type=1
            ).save()
            rank += 1
        duration_rank = 1
        for m in MamaCarryTotal.get_duration_ranking_list()[0:500]:
            c = CarryTotalRecord.objects.get_or_create(
                stat_time=stat_time,
                mama=m)
            c.history_total = m.history_total
            c.duration_total = m.duration_total
            c.duration_rank = duration_rank
            c.save()
            duration_rank += 1

    @staticmethod
    def snapshot_per_week(record_week):
        """
            record_week: 统计的周
        :param record_week:
        :return:
        """
        moves = []
        for i in MamaCarryTotal.objects.filter(stat_time=STAT_TIME):
            c = CarryTotalRecord.create(i, save=False, record_time=record_week, type=1)
            moves.append(c)
        CarryTotalRecord.objects.bulk_create(moves)

    @staticmethod
    def get_activity_ranking_list():
        """
            一元开店，取一元妈妈活动总收益（预期收益+确定收益）排名
        """
        return MamaCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL,
                                             last_renew_type=XiaoluMama.TRIAL, stat_time=datetime.datetime(2016,7,29,0)).order_by(
            (F('duration_total') + F('expect_total')).desc())


class TeamCarryTotalRecord(BaseModel):
    """
        活动记录
    """
    mama = models.ForeignKey(XiaoluMama)
    last_renew_type = models.IntegerField(choices=XiaoluMama.RENEW_TYPE, default=365, db_index=True,
                                          verbose_name=u"最近续费类型")
    agencylevel = models.IntegerField(default=XiaoluMama.INNER_LEVEL, db_index=True, choices=XiaoluMama.AGENCY_LEVEL,
                                      verbose_name=u"代理类别")
    stat_time = models.DateTimeField(default=STAT_TIME, db_index=True, verbose_name=u'统计起始时间')
    total_rank = models.IntegerField(default=0, verbose_name=u'总额排名')
    duration_rank = models.IntegerField(default=0, verbose_name=u'活动期间排名')
    total = models.IntegerField(default=0, verbose_name=u'团队收益总额', help_text=u'单位为分')
    duration_total = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    expect_total = models.IntegerField(default=0, verbose_name=u'统计期间预期收益总额', help_text=u'单位为分')
    num = models.IntegerField(default=0, db_index=True, verbose_name=u'团队订单数量')
    duration_num = models.IntegerField(default=0, verbose_name=u'活动期间团队订单数量')
    expect_num = models.IntegerField(default=0, verbose_name=u'统计期间预期订单数量')
    mama_ids = JSONCharMyField(max_length=10240, blank=True, default='[]', verbose_name=u'相关妈妈')
    record_time = models.DateTimeField(null=True, db_index=True, verbose_name=u'记录批次时间')
    type = models.IntegerField(default=0, db_index=True, choices=((0, u'每周统计'), (1, u'活动统计')))

    class Meta:
        db_table = 'xiaolumm_team_carry_total_record'
        app_label = 'xiaolumm'
        verbose_name = u'妈妈团队收益排名记录'
        verbose_name_plural = u'妈妈团队收益排名记录'

    @staticmethod
    def create(team_carry_total, record_time=datetime.datetime.now(), save=True):
        record = TeamCarryTotalRecord(
            mama_id=team_carry_total.mama_id,
            last_renew_type=team_carry_total.last_renew_type,
            agencylevel=team_carry_total.agencylevel,
            stat_time=team_carry_total.stat_time,
            record_time=record_time,
            total_rank=team_carry_total.total_rank,
            duration_rank=team_carry_total.duration_rank,
            total=team_carry_total.total,
            duration_total=team_carry_total.duration_total,
            num=team_carry_total.num,
            duration_num=team_carry_total.duration_num,
            mama_ids=team_carry_total.mama_ids
        )
        if save:
            record.save()
        return record


class RankActivity(AdminModel):
    start_time = models.DateField(verbose_name=u'活动开始时间', help_text=u'9月12日0点开始则选9月12日')
    end_time = models.DateField(verbose_name=u'活动结束时间', help_text=u'9月14日0点结束则选9月13日')
    STATUS_CHOICES = ((0, u'准备'), (1, u'有效'), (2, u'结束'), (3, u'作废'))
    status = models.IntegerField(default=1, verbose_name=u'状态')
    note = models.CharField(max_length=100, verbose_name=u'备注')

    class Meta:
        db_table = 'xiaolumm_rank_activity'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈收益排名活动'
        verbose_name_plural = u'小鹿妈妈收益排名活动列表'

    @staticmethod
    def now_activity():
        _now = datetime.datetime.now()
        return RankActivity.objects.filter(start_time__lte=_now, end_time__gte=_now, status=1).first()

    def is_active(self):
        _now = datetime.datetime.now()
        return self.start_time <= _now.date() <= self.end_time


def getattr_change(instance, target):
    if target == 'activity_duration_total':
        return getattr(instance, 'duration_total')
    return getattr(instance, target)


class ActivityRankTotal(object):
    @property
    def duration_total_display(self):
        return '%.2f' % (self.duration_total * 0.01)

    @property
    def duration_rank(self):
        if not self.activity.is_active():
            return self.duration_rank_delay
        if self._redis_duration_total_cache_ and str(self.mama_id) in self._redis_duration_total_cache_:
            return self._redis_duration_total_cache_.get(str(self.mama_id))
        cache_rank = STAT_RANK_REDIS.get_rank(type(self), 'duration_total', self.mama_id)
        if cache_rank is None:
            STAT_RANK_REDIS.update_cache(self, ['duration_total'])
            return self.duration_rank_delay
        else:
            return cache_rank

    @classmethod
    def check_update_cache(cls, target='duration_total'):
        if STAT_RANK_REDIS.is_locked(cls.__name__ + '-' + target):
            return
        cache_count = STAT_RANK_REDIS.get_rank_count(cls, target)
        condition = copy(cls.filters()[target])
        condition['activity_id'] = RankActivity.now_activity().id
        real_count = cls.objects.filter(**condition).count()
        if cache_count > real_count:
            logger.error('cache_count big than real_count')
            STAT_RANK_REDIS.clear_cache(cls, target)
            cache_mama_ids = []
        elif cache_count < real_count:
            cache_mama_ids = STAT_RANK_REDIS.get_rank_list(cls, target, 0, -1)
        if cache_count != real_count:
            res = {str(i.mama_id): getattr_change(i, target) for i in cls.objects.filter(**condition).exclude(mama_id__in=cache_mama_ids)}
            STAT_RANK_REDIS.batch_update_cache(res, cls, target)
            logger.error('some ' + cls.__name__ + ' cache has missed but now repaird:' + ','.join(res.keys()))
        STAT_RANK_REDIS.lock(cls.__name__ + '-' + target)

    @classmethod
    def get_duration_ranking_list(cls, begin_time=None):
        return cls.get_ranking_list(begin_time, order_field='duration_total')

    @classmethod
    def get_ranking_list(cls, rank_activity=None, order_field='total', start=0, end=100):
        if rank_activity.is_active():
            # 本周数据从redis获取
            # 检查缓存总数如果不符合则更新缓存
            cls.check_update_cache(order_field)
            rank_dict = STAT_RANK_REDIS.get_rank_dict(cls, order_field, start, end)
            condition = {'stat_time': rank_activity.start_time, order_field + '__gt': 0, 'mama_id__in': rank_dict.keys()}
            setattr(cls, '_redis_' + order_field + '_cache_', rank_dict)
        else:
            condition = {'stat_time': rank_activity.end_time, order_field + '__gt': 0}
        return cls.objects.filter(**condition).order_by('-' + order_field)


class ActivityMamaCarryTotal(BaseMamaCarryTotal, ActivityRankTotal):
    activity = models.ForeignKey(RankActivity, related_name='ranks', verbose_name=u'活动')
    mama = models.ForeignKey(XiaoluMama)
    duration_total = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    duration_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'活动期排名',
                                              help_text=u'单位为分，每日更新，从cache中可实时更新')
    activity_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'活动期排名',
                                              help_text=u'单位为分，每日更新，从cache中可实时更新')
    invite_trial_num = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    invite_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'活动期邀请数排名',
                                              help_text=u'单位为分，每日更新，从cache中可实时更新')
    _redis_duration_total_cache_ = {}
    _redis_activity_duration_total_cache_ = {}
    _redis_invite_trial_num_cache_ = {}

    class Meta:
        unique_together = ('mama', 'activity')
        db_table = 'xiaolumm_activity_carry_total'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈活动收益排名'
        verbose_name_plural = u'小鹿妈妈活动收益排名列表'

    @staticmethod
    def filters():
        return {
            'duration_total': {
                'agencylevel__gt': XiaoluMama.INNER_LEVEL,
            },
            'activity_duration_total':{
                'agencylevel__gt': XiaoluMama.INNER_LEVEL,
                'last_renew_type': 15
            },
            'invite_trial_num': {
                'agencylevel__gt': XiaoluMama.INNER_LEVEL,
            }
        }

    def update_activity_rank(self):
        if self.last_renew_type == 15:
            STAT_RANK_REDIS.update_cache(self, ['activity_duration_total'], func=getattr_change)

    @property
    def activity_rank(self):
        if not self.activity.is_active():
            return self.activity_rank_delay
        if self._redis_activity_duration_total_cache_ and str(self.mama_id) in self._redis_activity_duration_total_cache_:
            return self._redis_activity_duration_total_cache_.get(str(self.mama_id))
        cache_rank = STAT_RANK_REDIS.get_rank(type(self), 'activity_duration_total', self.mama_id)
        if self.activity_rank_delay == 0 and cache_rank is None:
            return 0
        elif cache_rank is None:
            return self.update_activity_rank()
        else:
            return cache_rank

    @property
    def invite_rank(self):
        if not self.activity.is_active():
            return self.invite_rank_delay
        if self._redis_invite_trial_num_cache_ and str(self.mama_id) in self._redis_invite_trial_num_cache_:
            return self._redis_invite_trial_num_cache_.get(str(self.mama_id))
        cache_rank = STAT_RANK_REDIS.get_rank(type(self), 'invite_trial_num', self.mama_id)
        if cache_rank is None:
            STAT_RANK_REDIS.update_cache(self, ['invite_trial_num'])
            return self.invite_rank_delay
        else:
            return cache_rank

    def set_data(self, activity):
        cr_conditions = {
            'date_field__gte': activity.start_time,
            'date_field__lte': activity.end_time,
            'mama_id': self.mama_id,
            'status__in': [1, 2]
        }
        duration_total = CarryRecord.objects.filter(**cr_conditions).aggregate(
            total=Sum('carry_num')).get('total') or 0
        self.duration_total = duration_total
        self.invite_trial_num = MamaFortune.objects.get(mama_id=self.mama_id).invite_trial_num

    @staticmethod
    def reset_rank(activity, target='duration_total'):
        target_fields = {'duration_total': 'duration_rank_delay',
                         'activity_duration_total': 'activity_rank_delay',
                         'invite_trial_num': 'invite_rank_delay'}
        if target not in target_fields:
            raise Exception('target field err')
        target_condition = {'duration_total':{'activity_id': activity.id},
                            'activity_duration_total': {'activity_id': activity.id, 'last_renew_type':15},
                            'invite_trial_num': {'activity_id': activity.id}}
        ActivityMamaCarryTotal.batch_generate(activity)
        i = 1
        rank = 1
        last_value = None
        res = {}
        for m in ActivityMamaCarryTotal.objects.filter(**target_condition[target]).order_by('-' + target). \
                values('mama_id', target):
            if last_value is None or m[target] < last_value:
                last_value = m[target]
                rank = i
            res[m['mama_id']] = rank if last_value > 0 else 0
            i += 1
        multi_update(ActivityMamaCarryTotal, 'mama_id', target_fields[target], res,
                     'activity_id="%s"' % (activity.id,))

    @staticmethod
    def update_or_create(activity, mama_id):
        ins = activity.ranks.filter(mama_id=mama_id).first()
        if ins:
            ins.set_data(activity)
            ins.save()
            return ins
        else:
            xlmm = XiaoluMama.objects.filter(pk=mama_id, progress__in=[XiaoluMama.PAY, XiaoluMama.PASS],
                                               status__in=[XiaoluMama.EFFECT, XiaoluMama.FROZEN], charge_status=XiaoluMama.CHARGED, is_staff=False).first()
            if xlmm:
                ins = ActivityMamaCarryTotal(
                    activity=activity,
                    mama_id=mama_id,
                    last_renew_type=xlmm.last_renew_type,
                    agencylevel=xlmm.agencylevel,
                )
                ins.set_data(activity)
                ins.save()
                return ins

    @staticmethod
    def reset_rank_invite(week_begin_time=None):
        ActivityMamaCarryTotal.reset_rank(week_begin_time, target='invite_trial_num')

    @staticmethod
    def batch_generate(activity):
        mama_data_ = XiaoluMama.objects.filter(progress__in=[XiaoluMama.PAY, XiaoluMama.PASS],
                                               status__in=[XiaoluMama.EFFECT, XiaoluMama.FROZEN], charge_status=XiaoluMama.CHARGED, is_staff=False). \
            values('id', 'last_renew_type', 'agencylevel')
        mama_data = {i['id']: i for i in mama_data_}
        mama_ids = mama_data.keys()
        exist_ids = [m['mama_id'] for m in
                     ActivityMamaCarryTotal.objects.filter(activity_id=activity.id).values('mama_id')]
        fortune_dict = {m.mama_id: m for m in MamaFortune.objects.filter(mama_id__in=mama_ids)}
        # 做下交集，避免fortune不存在的情况出错
        mama_ids = list(set(mama_ids) & set(fortune_dict.keys()) - set(exist_ids))
        cr_conditions = {
            'date_field__gte': activity.start_time,
            'date_field__lt': activity.end_time,
            'status__in': [1, 2]
        }
        duration_totals = CarryRecord.objects.filter(**cr_conditions).values('mama_id').annotate(total=Sum('carry_num'))
        duration_total_dict = {i['mama_id']: i['total'] for i in duration_totals}
        records = []
        for mmid in mama_ids:
            wm = ActivityMamaCarryTotal(
                activity=activity,
                mama_id=mmid,
                last_renew_type=mama_data.get(mmid).get('last_renew_type'),
                agencylevel=mama_data.get(mmid).get('agencylevel'),
                invite_trial_num=fortune_dict[mmid].invite_trial_num,
                duration_total=duration_total_dict.get(mmid, 0),
            )
            records.append(wm)
        ActivityMamaCarryTotal.objects.bulk_create(records)
        ActivityMamaCarryTotal.check_update_cache('invite_trial_num')
        ActivityMamaCarryTotal.check_update_cache('duration_total')
        ActivityMamaCarryTotal.check_update_cache('activity_duration_total')
        return len(records)

    @classmethod
    def get_ranking_list(cls, rank_activity=None, order_field='duration_total', start=0, end=100):
        if not rank_activity:
            rank_activity = RankActivity.now_activity()
        if rank_activity == RankActivity.now_activity():
            # 本周数据从redis获取
            # 检查缓存总数如果不符合则更新缓存
            cls.check_update_cache(order_field)
            rank_dict = STAT_RANK_REDIS.get_rank_dict(cls, order_field, start, end)
            condition = {'activity_id': rank_activity.id, 'mama_id__in': rank_dict.keys()}
            if order_field == 'activity_duration_total':
                condition['duration_total__gt'] = 0
                condition['last_renew_type'] = 15
            setattr(cls, '_redis_' + order_field + '_cache_', rank_dict)
        else:
            condition = {'activity_id': rank_activity.id, order_field + '__gt': 0}
        res = cls.objects.filter(**condition)
        if order_field == 'activity_duration_total':
            return res.order_by('-duration_total', 'mama_id')
        return res.order_by('-' + order_field, 'mama_id')


def update_activity_mama_carry_total_cache(sender, instance, created, **kwargs):
    # 当周数据实时更新到redis，从redis读取
    if instance.activity.is_active():
        mama = instance.mama
        activity = instance.activity
        mm_ids = [r.mama_id for r in activity.ranks.filter(mama_id__in=mama.get_family_memeber_ids())]
        for mid in mm_ids:
            team = ActivityMamaTeamCarryTotal.objects.filter(mama_id=mid, activity=activity).first()
            if not team:
                ActivityMamaTeamCarryTotal.generate(mama, activity)
            else:
                if instance.mama_id not in team.mama_ids:
                    team.reset_mama_ids()
                team.restat(team.mama_ids, activity)
                team.save()
        for target in ActivityMamaCarryTotal.filters():
            condtion = copy(ActivityMamaCarryTotal.filters()[target])
            condtion['pk'] = instance.pk
            if ActivityMamaCarryTotal.objects.filter(**condtion).exists():
                STAT_RANK_REDIS.update_cache(instance, [target], func=getattr_change)

post_save.connect(update_activity_mama_carry_total_cache,
                  sender=ActivityMamaCarryTotal, dispatch_uid='post_save_update_activity_mama_carry_total_cache')


class ActivityMamaTeamCarryTotal(BaseMamaTeamCarryTotal, ActivityRankTotal):
    activity = models.ForeignKey(RankActivity, related_name='teamranks', verbose_name=u'活动')
    mama = models.ForeignKey(XiaoluMama)
    member_ids = JSONCharMyField(default=[], max_length=10240, verbose_name=u'成员列表')
    duration_total = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    duration_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'活动期排名',
                                              help_text=u'单位为分，每日更新，从cache中可实时更新')
    activity_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'活动期排名',
                                              help_text=u'单位为分，每日更新，从cache中可实时更新')
    _redis_duration_total_cache_ = {}

    class Meta:
        unique_together = ('mama', 'activity')
        db_table = 'xiaolumm_activity_team_carry_total'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈活动收益排名'
        verbose_name_plural = u'小鹿妈妈活动收益排名列表'

    @classmethod
    def filters(cls):
        return {
            'duration_total': {
                'agencylevel__gt': XiaoluMama.INNER_LEVEL,
            }
        }
    @property
    def mama_ids(self):
        return self.member_ids

    def restat(self, mama_ids, activity):
        res = activity.ranks.filter(mama_id__in=mama_ids).aggregate(duration_total=Sum('duration_total'))
        self.duration_total = res.get('duration_total') or 0

    @staticmethod
    @transaction.atomic
    def get_by_mama_id(mama_id):
        RankActivity.objects.order_by()
        ActivityMamaTeamCarryTotal.objects.filter(mama_id)
        return

    @staticmethod
    def get_member_ids(mama, activity):
        mama_ids = [mama.mama_id for mama in activity.ranks.filter(mama_id__in=mama.get_team_member_ids())]
        return mama_ids

    @staticmethod
    def generate(mama, activity, save=True):
        if type(mama) != XiaoluMama:
            mama = XiaoluMama.objects.get(id=mama)
        mama_id = mama.id
        m = ActivityMamaTeamCarryTotal(
            mama_id=mama_id,
            last_renew_type=mama.last_renew_type,
            agencylevel=mama.agencylevel,
            activity=activity
        )
        m.member_ids = ActivityMamaTeamCarryTotal.get_member_ids(mama, activity)
        m.restat(m.member_ids, activity)
        if save:
            m.save()
        return m

    @staticmethod
    def batch_generate(activity):
        ActivityMamaCarryTotal.batch_generate(activity)
        mids = [m['mama_id'] for m in activity.ranks.values('mama_id')]
        tmids = [m['mama_id'] for m in activity.teamranks.values('mama_id')]
        left_ids = list(set(mids) - set(tmids))
        for mama_id in left_ids:
            ActivityMamaTeamCarryTotal.generate(mama_id, activity)
        return len(left_ids)

    @classmethod
    def get_ranking_list(cls, rank_activity=None, order_field='duration_total', start=0, end=100):
        if not rank_activity:
            rank_activity = RankActivity.now_activity()
        if rank_activity == RankActivity.now_activity():
            # 本周数据从redis获取
            # 检查缓存总数如果不符合则更新缓存
            cls.check_update_cache(order_field)
            rank_dict = STAT_RANK_REDIS.get_rank_dict(cls, order_field, start, end)
            condition = {'activity_id': rank_activity.id, 'duration_total__gt':0, 'mama_id__in': rank_dict.keys()}
            setattr(cls, '_redis_' + order_field + '_cache_', rank_dict)
        else:
            condition = {'activity_id': rank_activity.id, order_field + '__gt': 0}
        res = cls.objects.filter(**condition)
        return res.order_by('-' + order_field, 'mama_id')

    def reset_mama_ids(self):
        activity = RankActivity.now_activity()
        mmids = ActivityMamaTeamCarryTotal.get_member_ids(self.mama, activity)
        if self.member_ids != mmids:
            self.member_ids = mmids
        self.save()

def update_activity_mama_team_carry_total_cache(sender, instance, created, **kwargs):
    # 当周数据实时更新到redis，从redis读取
    STAT_RANK_REDIS.update_cache(instance, ['duration_total'])

post_save.connect(update_activity_mama_team_carry_total_cache,
                  sender=ActivityMamaCarryTotal, dispatch_uid='post_save_update_activity_mama_team_carry_total_cache')