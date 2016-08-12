# coding=utf-8
import datetime
from django.db import models
from django.db.models import Sum, F, Count, Q
from flashsale.xiaolumm.models import XiaoluMama, MamaFortune
from flashsale.xiaolumm.models.models_fortune import CarryRecord
from flashsale.xiaolumm.models.carry_total import BaseMamaCarryTotal, BaseMamaTeamCarryTotal, multi_update

"""
    carry_total开发的时候需求认识不够清晰，做的过于复杂
    目前看来，排名只有两类，一类是总额排名，一类是活动期排名，从对象角度说，是个人排名和团队排名，把握这几点即可
"""


class WeekTime(object):
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


class WeekMamaCarryTotal(BaseMamaCarryTotal):
    mama = models.ForeignKey(XiaoluMama)
    stat_time = models.DateTimeField(db_index=True, verbose_name=u'统计起始时间')
    total = models.IntegerField(default=0, verbose_name=u'收益总额', help_text=u'单位为分')
    duration_total = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    order_num = models.IntegerField(default=0, db_index=True, verbose_name=u'历史订单数量')
    total_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'总排名',
                                           help_text=u'单位为分,每日更新，从cache中可实时更新')
    duration_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'活动期排名',
                                              help_text=u'单位为分，每日更新，从cache中可实时更新')

    class Meta:
        unique_together = ('mama', 'stat_time')
        db_table = 'xiaolumm_week_carry_total'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈收益排名'
        verbose_name_plural = u'小鹿妈妈收益排名列表'

    @property
    def duration_total_display(self):
        return '%.2f' % (self.duration_total * 0.01)

    @property
    def total_display(self):
        return float('%.2f' % (self.total * 0.01))

    @property
    def total_rank(self):
        return self.total_rank_delay if self.total_rank_delay else 0

    @property
    def duration_rank(self):
        return self.duration_rank_delay if self.duration_rank_delay else 0

    @staticmethod
    def batch_generate(week_begin_time=None):
        week_begin_time = week_begin_time if WeekTime.check_week_begin(week_begin_time) else WeekTime.this_week_time()
        mama_data_ = XiaoluMama.objects.filter(progress__in=[XiaoluMama.PAY, XiaoluMama.PASS],
                                               status=XiaoluMama.EFFECT, charge_status=XiaoluMama.CHARGED).values('id',
                                                                                                                  'last_renew_type',
                                                                                                                  'agencylevel')
        mama_data = {i['id']: i for i in mama_data_}
        mama_ids = mama_data.keys()
        exist_ids = [m['mama_id'] for m in
                     WeekMamaCarryTotal.objects.filter(stat_time=week_begin_time).values('mama_id')]
        mama_ids = list(set(mama_ids) - set(exist_ids))
        fortune_dict = {m.id: m for m in MamaFortune.objects.filter(id__in=mama_ids)}
        cr_conditions = {
            'date_field__gte': week_begin_time,
            'status__in': [1, 2]
        }
        if week_begin_time <= WeekTime.last_week_time():
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
                total=fortune_dict.get(mmid).cash_total if fortune_dict.get(mmid) else 0,
                stat_time=week_begin_time,
                duration_total=duration_total_dict.get(mmid, 0),
            )
            records.append(wm)
        WeekMamaCarryTotal.objects.bulk_create(records)
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
        if stat_time <= WeekTime.last_week_time():
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
            'mama_id': self.mama_id,
            'status__in': [1, 2]
        }
        if self.stat_time <= WeekTime.last_week_time():
            next_week_time = self.stat_time + datetime.timedelta(days=7)
            cr_conditions['date_field__lt'] = next_week_time
        duration_total = CarryRecord.objects.filter(**cr_conditions).aggregate(
            total=Sum('carry_num')).get('total') or 0
        self.total = MamaFortune.get_by_mamaid(self.mama_id).cash_total
        self.duration_total = duration_total

    @staticmethod
    def batch_update():
        this_week_time = WeekTime.this_week_time()
        CarryRecord.objects.filter(date_field__gte=this_week_time).values('mama_id').annotate(Sum())

    @staticmethod
    def reset_rank(week_begin_time=None, target='total'):
        target_fields = {'total': 'total_rank_delay', 'duration_total': 'duration_rank_delay'}
        if target not in target_fields: raise Exception('target field err')
        week_begin_time = week_begin_time if WeekTime.check_week_begin(week_begin_time) else WeekTime.this_week_time()
        WeekMamaCarryTotal.batch_generate(week_begin_time)
        i = 1
        rank = 1
        last_value = None
        res = {}
        for m in WeekMamaCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL,
                                                   stat_time=week_begin_time).order_by('-' + target). \
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
    def get_rank_add(mama_id):
        week_begin_time = WeekMamaCarryTotal.this_week_time()
        last_week_time = WeekTime.last_week_time()
        week_begin_time = WeekMamaCarryTotal.objects.filter(mama_id=mama_id, stat_time=week_begin_time).first()
        last_week_time = WeekMamaCarryTotal.objects.filter(mama_id=mama_id, stat_time=last_week_time).first()
        if not week_begin_time or not last_week_time:
            return 0
        else:
            return week_begin_time.total_rank_delay - last_week_time.total_rank_delay

    @staticmethod
    def update_or_create(mama_id, week_begin_time=None):
        """
            更新数据以更新排名-其实这个方法尽可能更新了需要的数，唯独不更新排名
            排名更新在post_save事件中，15分钟以后，由celery事件更新排名。
        """
        week_begin_time = week_begin_time if WeekTime.check_week_begin(week_begin_time) else WeekTime.this_week_time()
        if not WeekMamaCarryTotal.objects.filter(mama_id=mama_id, stat_time=week_begin_time).exists():
            return WeekMamaCarryTotal.generate(mama_id, stat_time=week_begin_time)
        rank = WeekMamaCarryTotal.objects.get(mama_id=mama_id, stat_time=week_begin_time)
        rank.set_data()
        rank.save()
        return rank

    @staticmethod
    def get_ranking_list(week_begin_time=None, order_field='total_rank_delay'):
        week_begin_time = week_begin_time if WeekTime.check_week_begin(week_begin_time) else WeekTime.this_week_time()
        contidion = {'stat_time': week_begin_time, order_field + '__gt': 0}
        return WeekMamaCarryTotal.objects.filter(**contidion).order_by(order_field)

    @staticmethod
    def get_duration_ranking_list(week_begin_time=None):
        return WeekMamaCarryTotal.get_ranking_list(week_begin_time, order_field='duration_rank_delay')


class WeekMamaTeamCarryTotal(BaseMamaTeamCarryTotal):
    """
        周团队总额记录
    """
    mama = models.ForeignKey(XiaoluMama)
    stat_time = models.DateTimeField(db_index=True, verbose_name=u'统计起始时间')
    members = models.ManyToManyField(WeekMamaCarryTotal, related_name='teams')
    total = models.IntegerField(default=0, verbose_name=u'团队收益总额', help_text=u'单位为分')
    duration_total = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    total_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'总排名',
                                           help_text=u'单位为分,每日更新，从cache中可实时更新')
    duration_rank_delay = models.IntegerField(default=0, db_index=True, verbose_name=u'活动期排名',
                                              help_text=u'单位为分，每日更新，从cache中可实时更新')

    class Meta:
        unique_together = ('mama', 'stat_time')
        db_table = 'xiaolumm_week_team_carry_total'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈团队周收益排名'
        verbose_name_plural = u'小鹿妈妈团队周收益排名列表'

    @property
    def duration_total_display(self):
        return '%.2f' % (self.duration_total * 0.01)

    @property
    def total_display(self):
        return float('%.2f' % (self.total * 0.01))

    @property
    def total_rank(self):
        return self.total_rank_delay if self.total_rank_delay else 0

    @property
    def duration_rank(self):
        return self.duration_rank_delay if self.duration_rank_delay else 0

    @staticmethod
    def batch_generate(week_begin_time=None):
        week_begin_time = week_begin_time if WeekTime.check_week_begin(week_begin_time) else WeekTime.this_week_time()
        WeekMamaCarryTotal.batch_generate(week_begin_time)
        mids = [m['mama_id'] for m in WeekMamaCarryTotal.objects.values('mama_id')]
        tmids = [m['mama_id'] for m in WeekMamaTeamCarryTotal.objects.values('mama_id')]
        left_ids = list(set(mids) - set(tmids))
        for mama_id in left_ids:
            WeekMamaTeamCarryTotal.generate(mama_id, week_begin_time)
        return len(left_ids)

    @staticmethod
    def generate(mama, week_begin_time):
        if type(mama) != XiaoluMama:
            mama = XiaoluMama.objects.get(id=mama)
        mama_id = mama.id
        mama_ids = mama.get_team_member_ids()
        m = WeekMamaTeamCarryTotal(
            mama_id=mama_id,
            last_renew_type=mama.last_renew_type,
            agencylevel=mama.agencylevel,
            stat_time=week_begin_time
        )
        m.restat(mama_ids, week_begin_time)
        m.save()
        for mama in WeekMamaCarryTotal.objects.filter(mama_id__in=mama_ids, stat_time=week_begin_time):
            m.members.add(mama)
        m.save()
        return m

    def restat(self, mama_ids, stat_time):
        res = WeekMamaCarryTotal.objects.filter(mama_id__in=mama_ids, stat_time=stat_time).aggregate(
            total=Sum('total'),
            duration_total=Sum('duration_total'),
        )
        self.total = res.get('total') or 0
        self.duration_total = res.get('duration_total') or 0

    @staticmethod
    def get_rank_add(mama_id):
        week_begin_time = WeekMamaTeamCarryTotal.this_week_time()
        last_week_time = WeekTime.last_week_time()
        week_begin_time = WeekMamaTeamCarryTotal.objects.filter(mama_id=mama_id, stat_time=week_begin_time).first()
        last_week_time = WeekMamaTeamCarryTotal.objects.filter(mama_id=mama_id, stat_time=last_week_time).first()
        if not week_begin_time or not last_week_time:
            return 0
        else:
            return week_begin_time.total_rank_delay - last_week_time.total_rank_delay

    @staticmethod
    def reset_rank(week_begin_time=None, target='total'):
        target_fields = {'total': 'total_rank_delay', 'duration_total': 'duration_rank_delay'}
        if target not in target_fields: raise Exception('target field err')
        week_begin_time = week_begin_time if WeekTime.check_week_begin(week_begin_time) else WeekTime.this_week_time()
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
    def get_ranking_list(week_begin_time=None, order_field='total_rank_delay'):
        week_begin_time = week_begin_time if WeekTime.check_week_begin(week_begin_time) else WeekTime.this_week_time()
        contidion = {'stat_time': week_begin_time, order_field + '__gt': 0}
        return WeekMamaTeamCarryTotal.objects.filter(**contidion).order_by(order_field)

    @staticmethod
    def get_duration_ranking_list(week_begin_time=None):
        return WeekMamaTeamCarryTotal.get_ranking_list(week_begin_time, order_field='duration_rank_delay')

    @staticmethod
    def update_or_create(mama_id, stat_time=None):
        stat_time = stat_time if WeekTime.check_week_begin(stat_time) else WeekTime.this_week_time()
        if not WeekMamaTeamCarryTotal.objects.filter(mama_id=mama_id, stat_time=stat_time).exists():
            return WeekMamaTeamCarryTotal.generate(mama_id, stat_time)
        m = WeekMamaTeamCarryTotal.objects.filter(mama_id=mama_id, stat_time=stat_time).first()
        mama_ids = WeekMamaTeamCarryTotal.get_team_ids(mama_id)
        m.restat(mama_ids)
        m.save()
        now_mama_ids = [i['mama_id'] for i in m.members.values('mama_id')]
        left_mama_ids = list(set(mama_ids) - set(now_mama_ids))
        for mama in WeekMamaCarryTotal.objects.filter(mama_id__in=left_mama_ids):
            m.members.add(mama)
        m.save()
