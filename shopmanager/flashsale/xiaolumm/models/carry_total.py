# -*- coding:utf-8 -*-
import datetime
from django.db import models
from django.db.models import Sum, F, Count, Q
from django.db import connection
from django.db.models.signals import post_save
from core.models import BaseModel
from core.fields import JSONCharMyField
from flashsale.xiaolumm.models import XiaoluMama, MamaFortune, CashOut
from flashsale.xiaolumm.models.models_fortune import CarryRecord, OrderCarry, AwardCarry, ClickCarry, \
    MAMA_FORTUNE_HISTORY_LAST_DAY
from django.core.cache import cache

# 在下次活动前设置此处，以自动重设变更统计时间
STAT_TIME = datetime.datetime(2016, 7, 29)
STAT_END_TIME = datetime.datetime(2016, 8, 13)


# if datetime.datetime.now() < datetime.datetime(2016, 7, 28) \
# else datetime.datetime(2016, 7, 28)
class RankRedis(object):
    redis_cache = cache.get_master_client()

    def __init__(self, stat_time):
        self.stat_time = stat_time

    def get_cache_key(self, model_class, target='total'):
        return model_class.__name__ + '.' + self.stat_time.strftime('%Y%m%d') + '.' + target

    def update_cache(self, instance, targets=['duration_total', 'total']):
        for target in targets:
            RankRedis.redis_cache.zadd(self.get_cache_key(type(instance), target), instance.mama_id,
                                       getattr(instance, target))

    def batch_update_cache(self, instance, targets=['duration_total', 'total']):
        # TODO@hy 待优化 可一次性更新
        for target in targets:
            RankRedis.redis_cache.zadd(self.get_cache_key(type(instance), target), instance.mama_id,
                                       getattr(instance, target))

    def clear_cache(self, model_class, target):
        RankRedis.redis_cache.delete(self.get_cache_key(model_class, target))

    def get_rank_count(self, model_class, target):
        return RankRedis.redis_cache.zcard(self.get_cache_key(model_class, target))

    def get_rank_list(self, model_class, target, start, stop):
        return RankRedis.redis_cache.zrevrange(self.get_cache_key(model_class, target), start, stop)

    def get_rank_dict(self, model_class, target, start, stop):
        return dict(zip(RankRedis.redis_cache.zrevrange(self.get_cache_key(model_class, target), start, stop),
                        range(start + 1, stop + 1)))

    def get_rank(self, model_class, target, mama_id):
        rank = RankRedis.redis_cache.zrevrank(self.get_cache_key(model_class, target), mama_id)
        return rank + 1


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
        sum_res = CarryRecord.objects.filter(date_field__range=(STAT_TIME, STAT_END_TIME), mama_id=mama_id).exclude(
            status=CarryRecord.CANCEL). \
            values('status').annotate(total=Sum('carry_num'))
        sum_dict = {entry["status"]: entry["total"] for entry in sum_res}
        self.duration_total = sum_dict.get(CarryRecord.CONFIRMED, 0)
        self.expect_total = sum_dict.get(CarryRecord.PENDING, 0)
        if self.duration_total + self.expect_total:
            records = CarryRecord.objects.filter(date_field__gte=STAT_TIME, mama_id=mama_id,
                                                 status__in=[CarryRecord.PENDING, CarryRecord.CONFIRMED])
            self.carry_records = [c.id for c in records]
            sum_res = OrderCarry.objects.filter(mama_id=mama_id, status__in=[1, 2], created__gte=STAT_TIME). \
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
                                                        status=[XiaoluMama.EFFECT, XiaoluMama.FROZEN],
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


def update_carry_total_ranking(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks_mama_carry_total import task_update_carry_total_ranking, \
        task_update_carry_duration_total_ranking
    if datetime.datetime.now() > STAT_TIME:
        task_update_carry_total_ranking.delay()
        task_update_carry_duration_total_ranking.delay()


post_save.connect(update_carry_total_ranking,
                  sender=MamaCarryTotal, dispatch_uid='post_save_carrytotal_update_ranking')


def update_mama_carry_total_cache(sender, instance, created, **kwargs):
    # 当周数据实时更新到redis，从redis读取
    return
    if instance.stat_time == STAT_TIME:
        STAT_RANK_REDIS.update_cache(instance)


post_save.connect(update_mama_carry_total_cache,
                  sender=MamaCarryTotal, dispatch_uid='post_save_update_mama_carry_total_cache')


def update_team_carry_total(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks_mama_carry_total import task_update_team_carry_total
    if datetime.datetime.now() > STAT_TIME:
        for team in instance.teams.all():
            task_update_team_carry_total.delay(team.mama_id)


post_save.connect(update_team_carry_total,
                  sender=MamaCarryTotal, dispatch_uid='post_save_carrytotal_update_team_carry_total')


class BaseMamaTeamCarryTotal(BaseMamaCarryTotal):
    class Meta:
        abstract = True

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

    @classmethod
    def get_by_mama_id(cls, mama_id):
        if not cls.objects.filter(mama_id=mama_id).exists():
            return cls.generate(mama_id)
        return cls.objects.filter(mama_id=mama_id).first()


class MamaTeamCarryTotal(BaseMamaTeamCarryTotal):
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


post_save.connect(update_mama_carry_total_cache,
                  sender=MamaTeamCarryTotal, dispatch_uid='post_save_update_mama_team_carry_total_cache')


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
