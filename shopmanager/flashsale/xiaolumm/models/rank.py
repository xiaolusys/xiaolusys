# coding=utf-8
import datetime
from copy import copy
from django.db import models
from django.db.models import Sum, F, Count, Q
from django.db.models.signals import post_save
from core.fields import JSONCharMyField
from flashsale.xiaolumm.models import XiaoluMama, MamaFortune, ReferalRelationship
from flashsale.xiaolumm.models.models_fortune import CarryRecord
from flashsale.xiaolumm.models.carry_total import BaseMamaCarryTotal, BaseMamaTeamCarryTotal, multi_update, RankRedis
import logging

logger = logging.getLogger('django.request')

"""
    carry_total开发的时候需求认识不够清晰，做的过于复杂
    目前看来，排名只有两类，一类是总额排名，一类是活动期排名，从对象角度说，是个人排名和团队排名，把握这几点即可

    所有人都会在WeekMamaCarryTotal表或WeekMamaTeamCarryTotal表生成记录，但必须符合条件才可能进入到排名。
    用RankRedis的WEEK_RANK_REDIS实例来管理缓存数据。
    将涉及 “周排名”的通用方法都移动到WeekRank中以减少代码量。
"""


class WeekRank(object):
    @staticmethod
    def this_week_time():
        _now = datetime.datetime.now()
        return datetime.datetime(year=_now.year, month=_now.month, day=_now.day) - datetime.timedelta(
            days=_now.weekday())

    @staticmethod
    def last_week_time():
        _now = datetime.datetime.now()
        return datetime.datetime(year=_now.year, month=_now.month, day=_now.day) - datetime.timedelta(
            days=(7 + _now.weekday()))

    @staticmethod
    def check_week_begin(week_begin_time):
        if not week_begin_time:
            return False
        if not week_begin_time.weekday() == 0:
            raise Exception('week stat time mast begin at monday')
        if not week_begin_time.hour == week_begin_time.minute == week_begin_time.second == 0:
            raise Exception('week stat time mast begin at day begin')
        return True

    @property
    def duration_total_display(self):
        return '%.2f' % (self.duration_total * 0.01)

    @property
    def total_display(self):
        return float('%.2f' % (self.total * 0.01))

    @property
    def total_rank(self):
        if self.stat_time != WeekRank.this_week_time():
            return self.total_rank_delay
        if self._redis_total_cache_ and str(self.mama_id) in self._redis_total_cache_:
            # 批量操作时设置_redis_cache_，避免分开多次读取缓存
            return self._redis_total_cache_.get(str(self.mama_id))
        cache_rank = WEEK_RANK_REDIS.get_rank(type(self), 'total', self.mama_id)
        if cache_rank is None:
            WEEK_RANK_REDIS.update_cache(self, ['total'])
            return self.total_rank_delay
        else:
            return cache_rank

    @property
    def duration_rank(self):
        if self.stat_time != WeekRank.this_week_time():
            return self.duration_rank_delay
        if self._redis_duration_total_cache_ and str(self.mama_id) in self._redis_duration_total_cache_:
            return self._redis_duration_total_cache_.get(str(self.mama_id))
        cache_rank = WEEK_RANK_REDIS.get_rank(type(self), 'duration_total', self.mama_id)
        if cache_rank is None:
            WEEK_RANK_REDIS.update_cache(self, ['duration_total'])
            return self.duration_rank_delay
        else:
            return cache_rank

    @classmethod
    def get_rank_add(cls, mama_id):
        week_begin_time = cls.this_week_time()
        last_week_time = WeekRank.last_week_time()
        this_week = cls.objects.filter(mama_id=mama_id, stat_time=week_begin_time).first()
        last_week = cls.objects.filter(mama_id=mama_id, stat_time=last_week_time).first()
        if not this_week or not last_week:
            return 0
        else:
            return this_week.total_rank - last_week.total_rank_delay

    @classmethod
    def check_update_cache(cls, target='total'):
        this_week_time = WeekRank.this_week_time()
        cache_count = WEEK_RANK_REDIS.get_rank_count(cls, target)
        condition = copy(cls.filters[target])
        condition['stat_time'] = this_week_time
        real_count = cls.objects.filter(**condition).count()
        if cache_count > real_count:
            ori_cache_mama_ids = WEEK_RANK_REDIS.get_rank_list(cls, target, 0, -1)
            real_ids = [c['mama_id'] for c in cls.objects.filter(**condition).values('mama_id')]
            ids = set(ori_cache_mama_ids) - set(real_ids)
            id_str = ','.join([str(i) for i in list(ids)])
            logger.error('cache_count big than real_count' + '|' + cls.__name__ + '|' + target + ':' + id_str)
            WEEK_RANK_REDIS.clear_cache(cls, target)
            cache_mama_ids = []
        elif cache_count < real_count:
            cache_mama_ids = WEEK_RANK_REDIS.get_rank_list(cls, target, 0, -1)
        if cache_count != real_count:
            res = {str(i.mama_id): getattr(i, target) for i in cls.objects.filter(**condition).exclude(mama_id__in=cache_mama_ids)}
            WEEK_RANK_REDIS.batch_update_cache(res, cls, target)
            if cache_count < real_count:
                logger.error('some ' + cls.__name__ + '|' + target + '|' + ' cache has missed but now repaird:' + ','.join(res.keys()))

    @classmethod
    def get_duration_ranking_list(cls, week_begin_time=None):
        return cls.get_ranking_list(week_begin_time, order_field='duration_total')

    @classmethod
    def get_ranking_list(cls, week_begin_time=None, order_field='total', start=0, end=100):
        week_begin_time = week_begin_time if WeekRank.check_week_begin(week_begin_time) else WeekRank.this_week_time()
        if week_begin_time == WeekRank.this_week_time():
            # 本周数据从redis获取
            # 检查缓存总数如果不符合则更新缓存
            cls.check_update_cache(order_field)
            rank_dict = WEEK_RANK_REDIS.get_rank_dict(cls, order_field, start, end)
            condition = {'stat_time': week_begin_time, order_field + '__gt': 0, 'mama_id__in': rank_dict.keys()}
            setattr(cls, '_redis_' + order_field + '_cache_', rank_dict)
            return cls.objects.filter(**condition).order_by('-' + order_field)
        else:
            condition = {'stat_time': week_begin_time, order_field + '__gt': 0, 'agencylevel__gt': XiaoluMama.INNER_LEVEL}
            targets = {'total': 'total_rank_delay', 'duration_total':'duration_rank_delay'}
            return cls.objects.filter(**condition).order_by(targets[order_field])

    @classmethod
    def get_by_mama_id(cls, mama_id, week_begin_time):
        week_begin_time = week_begin_time if WeekRank.check_week_begin(week_begin_time) else WeekRank.this_week_time()
        return cls.objects.filter(mama_id=mama_id, stat_time=week_begin_time).first()


def get_week_rank_redis():
    return RankRedis(WeekRank.this_week_time())


WEEK_RANK_REDIS = get_week_rank_redis()


class WeekMamaCarryTotal(BaseMamaCarryTotal, WeekRank):
    filters = {
        'total': {
            'agencylevel__gt': XiaoluMama.INNER_LEVEL,
        },
        'duration_total': {
            'agencylevel__gt': XiaoluMama.INNER_LEVEL,
        }
    }
    mama = models.ForeignKey(XiaoluMama)
    stat_time = models.DateTimeField(db_index=True, verbose_name=u'统计起始时间')
    total = models.IntegerField(default=0, verbose_name=u'收益总额', help_text=u'单位为分')
    duration_total = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    order_num = models.IntegerField(default=0, db_index=True, verbose_name=u'历史订单数量')
    total_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'总排名',
                                           help_text=u'单位为分,每日更新，从cache中可实时更新')
    duration_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'活动期排名',
                                              help_text=u'单位为分，每日更新，从cache中可实时更新')
    _redis_total_cache_ = {}
    _redis_duration_total_cache_ = {}

    class Meta:
        unique_together = ('mama', 'stat_time')
        db_table = 'xiaolumm_week_carry_total'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈团队收益周排名'
        verbose_name_plural = u'小鹿妈妈团队收益周排名列表'

    @staticmethod
    def batch_generate(week_begin_time=None):
        week_begin_time = week_begin_time if WeekRank.check_week_begin(week_begin_time) else WeekRank.this_week_time()
        mama_data_ = XiaoluMama.objects.filter(progress__in=[XiaoluMama.PAY, XiaoluMama.PASS],
                                               status__in=[XiaoluMama.EFFECT, XiaoluMama.FROZEN], charge_status=XiaoluMama.CHARGED, is_staff=False). \
            values('id', 'last_renew_type', 'agencylevel')
        mama_data = {i['id']: i for i in mama_data_}
        mama_ids = mama_data.keys()
        exist_ids = [m['mama_id'] for m in
                     WeekMamaCarryTotal.objects.filter(stat_time=week_begin_time).values('mama_id')]
        fortune_dict = {m.mama_id: m for m in MamaFortune.objects.filter(mama_id__in=mama_ids)}
        # 做下交集，避免fortune不存在的情况出错
        mama_ids = list(set(mama_ids) & set(fortune_dict.keys()) - set(exist_ids))
        cr_conditions = {
            'date_field__gte': week_begin_time,
            'status__in': [1, 2]
        }
        if week_begin_time <= WeekRank.last_week_time():
            next_week_time = week_begin_time + datetime.timedelta(days=7)
            cr_conditions['date_field__lt'] = next_week_time
        duration_totals = CarryRecord.objects.filter(**cr_conditions).values('mama_id').annotate(
            total=Sum('carry_num'))
        duration_total_dict = {i['mama_id']: i['total'] for i in duration_totals}
        records = []
        for mmid in mama_ids:
            wm = WeekMamaCarryTotal(
                mama_id=mmid,
                last_renew_type=mama_data.get(mmid).get('last_renew_type'),
                agencylevel=mama_data.get(mmid).get('agencylevel'),
                total=fortune_dict[mmid].cash_total,
                order_num=fortune_dict[mmid].order_num,
                stat_time=week_begin_time,
                duration_total=duration_total_dict.get(mmid, 0),
            )
            records.append(wm)
        WeekMamaCarryTotal.objects.bulk_create(records)
        if week_begin_time == WeekRank.this_week_time():
            WeekMamaCarryTotal.check_update_cache('total')
            WeekMamaCarryTotal.check_update_cache('duration_total')
        return len(records)

    @staticmethod
    def generate(mama, stat_time):
        if type(mama) != XiaoluMama:
            mama = XiaoluMama.objects.get(id=mama)
        mmid = mama.id
        cr_conditions = {
            'date_field__gte': stat_time,
            'mama_id': mama.id,
            'status__in': [1, 2]
        }
        if stat_time <= WeekRank.last_week_time():
            next_week_time = stat_time + datetime.timedelta(days=7)
            cr_conditions['date_field__lt'] = next_week_time
        duration_total = CarryRecord.objects.filter(**cr_conditions).aggregate(
            total=Sum('carry_num')).get('total') or 0
        wm = WeekMamaCarryTotal(
            mama_id=mmid,
            last_renew_type=mama.last_renew_type,
            agencylevel=mama.agencylevel,
            total=MamaFortune.get_by_mamaid(mmid).cash_total,
            stat_time=stat_time,
            duration_total=duration_total
        )
        wm.save()
        return wm

    def set_data(self):
        cr_conditions = {
            'date_field__gte': self.stat_time,
            'date_field__lt': self.stat_time + datetime.timedelta(days=7),
            'mama_id': self.mama_id,
            'status__in': [1, 2]
        }
        duration_total = CarryRecord.objects.filter(**cr_conditions).aggregate(
            total=Sum('carry_num')).get('total') or 0
        self.total = MamaFortune.get_by_mamaid(self.mama_id).cash_total
        self.duration_total = duration_total

    @staticmethod
    def batch_update():
        this_week_time = WeekRank.this_week_time()
        CarryRecord.objects.filter(date_field__gte=this_week_time).values('mama_id').annotate(Sum())

    @staticmethod
    def reset_rank(week_begin_time=None, target='total'):
        target_fields = {'total': 'total_rank_delay', 'duration_total': 'duration_rank_delay'}
        if target not in target_fields:
            raise Exception('target field err')
        week_begin_time = week_begin_time if WeekRank.check_week_begin(week_begin_time) else WeekRank.this_week_time()
        target_condition = {key: dict(WeekMamaCarryTotal.filters[key].items() + [('stat_time', week_begin_time)]) for key in
                            WeekMamaCarryTotal.filters}
        WeekMamaCarryTotal.batch_generate(week_begin_time)
        i = 1
        rank = 1
        last_value = None
        res = {}
        for m in WeekMamaCarryTotal.objects.filter(**target_condition[target]).order_by('-' + target). \
                values('mama_id', target):
            if last_value is None or m[target] < last_value:
                last_value = m[target]
                rank = i
            res[m['mama_id']] = rank if last_value > 0 else 0
            i += 1
        multi_update(WeekMamaCarryTotal, 'mama_id', target_fields[target], res,
                     'stat_time="%s"' % (week_begin_time.strftime('%Y-%m-%d %H:%M:%S'),))

    @staticmethod
    def reset_rank_duration(week_begin_time=None):
        WeekMamaCarryTotal.reset_rank(week_begin_time, target='duration_total')

    @staticmethod
    def update_or_create(mama_id, week_begin_time=None):
        mama = XiaoluMama.objects.get(id=mama_id)
        if not mama.is_available_rank() or mama.is_staff:
            return
        week_begin_time = week_begin_time if WeekRank.check_week_begin(week_begin_time) else WeekRank.this_week_time()
        if not WeekMamaCarryTotal.objects.filter(mama_id=mama_id, stat_time=week_begin_time).exists():
            return WeekMamaCarryTotal.generate(mama_id, stat_time=week_begin_time)
        rank = WeekMamaCarryTotal.objects.get(mama_id=mama_id, stat_time=week_begin_time)
        rank.set_data()
        rank.save()
        return rank


def update_week_mama_carry_total_cache(sender, instance, created, **kwargs):
    # 当周数据实时更新到redis，从redis读取
    if WeekRank.this_week_time() == instance.stat_time:
        mama = instance.mama
        mm_ids = [r.mama_id for r in WeekMamaCarryTotal.objects.filter(stat_time=instance.stat_time, mama_id__in=mama.get_family_memeber_ids())]
        for mid in mm_ids:
            team = WeekMamaTeamCarryTotal.objects.filter(mama_id=mid, stat_time=instance.stat_time).first()
            if not team:
                WeekMamaTeamCarryTotal.generate(mama, instance.stat_time)
            else:
                if instance.mama_id not in team.mama_ids:
                    team.reset_mama_ids()
                team.restat(team.mama_ids, instance.stat_time)
                team.save()
        for target in WeekMamaCarryTotal.filters:
            condtion = copy(WeekMamaCarryTotal.filters[target])
            condtion['pk'] = instance.pk
            if WeekMamaCarryTotal.objects.filter(**condtion).exists():
                WEEK_RANK_REDIS.update_cache(instance, [target])

post_save.connect(update_week_mama_carry_total_cache,
                  sender=WeekMamaCarryTotal, dispatch_uid='post_save_update_week_mama_carry_total_cache')


class WeekMamaTeamCarryTotal(BaseMamaTeamCarryTotal, WeekRank):
    """
        周团队总额记录
    """
    filters = {
        'total': {
            'agencylevel__gt': XiaoluMama.INNER_LEVEL
        },
        'duration_total': {
            'agencylevel__gt': XiaoluMama.INNER_LEVEL
        }
    }
    mama = models.ForeignKey(XiaoluMama)
    stat_time = models.DateTimeField(db_index=True, verbose_name=u'统计起始时间')
    members = models.ManyToManyField(WeekMamaCarryTotal, related_name='teams')
    member_ids = JSONCharMyField(default=[], max_length=10240, verbose_name=u'成员列表')
    total = models.IntegerField(default=0, verbose_name=u'团队收益总额', help_text=u'单位为分')
    duration_total = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    total_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'总排名',
                                           help_text=u'单位为分,每日更新，从cache中可实时更新')
    duration_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'活动期排名',
                                              help_text=u'单位为分，每日更新，从cache中可实时更新')
    _redis_total_cache_ = {}
    _redis_duration_total_cache_ = {}

    class Meta:
        unique_together = ('mama', 'stat_time')
        db_table = 'xiaolumm_week_team_carry_total'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈团队周收益排名'
        verbose_name_plural = u'小鹿妈妈团队周收益排名列表'
    @property
    def mama_ids(self):
        return self.member_ids

    @staticmethod
    def batch_generate(week_begin_time=None):
        week_begin_time = week_begin_time if WeekRank.check_week_begin(week_begin_time) else WeekRank.this_week_time()
        WeekMamaCarryTotal.batch_generate(week_begin_time)
        mids = [m['mama_id'] for m in WeekMamaCarryTotal.objects.filter(stat_time=week_begin_time).values('mama_id')]
        tmids = [m['mama_id'] for m in WeekMamaTeamCarryTotal.objects.filter(stat_time=week_begin_time).values('mama_id')]
        left_ids = list(set(mids) - set(tmids))
        for mama_id in left_ids:
            WeekMamaTeamCarryTotal.generate(mama_id, week_begin_time)
        return len(left_ids)

    @staticmethod
    def get_member_ids(mama, week_begin_time):
        mama_ids = [mama.mama_id for mama in WeekMamaCarryTotal.objects.filter(mama_id__in=mama.get_team_member_ids(), stat_time=week_begin_time)]
        return mama_ids

    @staticmethod
    def generate(mama, week_begin_time):
        if type(mama) != XiaoluMama:
            mama = XiaoluMama.objects.get(id=mama)
        mama_id = mama.id
        m = WeekMamaTeamCarryTotal(
            mama_id=mama_id,
            last_renew_type=mama.last_renew_type,
            agencylevel=mama.agencylevel,
            stat_time=week_begin_time
        )
        m.member_ids = WeekMamaTeamCarryTotal.get_member_ids(mama, week_begin_time)
        m.restat(m.member_ids, week_begin_time)
        m.save()
        return m

    def restat(self, mama_ids, stat_time):
        res = WeekMamaCarryTotal.objects.filter(mama_id__in=mama_ids, stat_time=stat_time).aggregate(
            total=Sum('total'), duration_total=Sum('duration_total'))
        self.total = res.get('total') or 0
        self.duration_total = res.get('duration_total') or 0

    @staticmethod
    def reset_rank(week_begin_time=None, target='total'):
        target_fields = {'total': 'total_rank_delay', 'duration_total': 'duration_rank_delay'}
        if target not in target_fields:
            raise Exception('target field err')
        week_begin_time = week_begin_time if WeekRank.check_week_begin(week_begin_time) else WeekRank.this_week_time()
        WeekMamaTeamCarryTotal.batch_generate(week_begin_time)
        i = 1
        rank = 1
        last_value = None
        res = {}
        for m in WeekMamaTeamCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL,
                                                       stat_time=week_begin_time).order_by('-' + target). \
                values('mama_id', target):
            if last_value is None or m[target] < last_value:
                last_value = m[target]
                rank = i
            res[m['mama_id']] = rank if last_value > 0 else 0
            i += 1
        multi_update(WeekMamaTeamCarryTotal, 'mama_id', target_fields[target], res,
                     'stat_time="%s"' % (week_begin_time.strftime('%Y-%m-%d %H:%M:%S'),))

    @staticmethod
    def reset_rank_duration(week_begin_time=None):
        WeekMamaTeamCarryTotal.reset_rank(week_begin_time, target='duration_total')

    @staticmethod
    def get_duration_ranking_list(week_begin_time=None):
        return WeekMamaTeamCarryTotal.get_ranking_list(week_begin_time, order_field='duration_total')

    @staticmethod
    def update_or_create(mama_id, stat_time=None):
        stat_time = stat_time if WeekRank.check_week_begin(stat_time) else WeekRank.this_week_time()
        if not WeekMamaTeamCarryTotal.objects.filter(mama_id=mama_id, stat_time=stat_time).exists():
            return WeekMamaTeamCarryTotal.generate(mama_id, stat_time)
        m = WeekMamaTeamCarryTotal.objects.filter(mama_id=mama_id, stat_time=stat_time).first()
        mama_ids = WeekMamaTeamCarryTotal.get_member_ids(mama_id, stat_time)
        m.member_ids = mama_ids
        m.restat(mama_ids)
        m.save()

    def check_add_member(self, mama):
        if mama.id not in self.member_ids:
            self.member_ids = WeekMamaTeamCarryTotal.get_member_ids(mama, WeekRank.this_week_time())
            self.save()

    def reset_mama_ids(self):
        mmids = WeekMamaTeamCarryTotal.get_member_ids(self.mama, self.stat_time)
        if self.member_ids != mmids:
            self.member_ids = mmids
        self.save()

def update_week_team_mama_carry_total_cache(sender, instance, created, **kwargs):
    WEEK_RANK_REDIS.update_cache(instance, ['total', 'duration_total'])

post_save.connect(update_week_team_mama_carry_total_cache,
                  sender=WeekMamaTeamCarryTotal, dispatch_uid='post_save_update_week_mama_team_carry_total_cache')