# -*- coding:utf-8 -*-
import datetime
from django.db import models
from django.db.models import Sum, F
from django.db import connection
from django.db.models.signals import post_save
from core.models import BaseModel
from core.fields import JSONCharMyField
from flashsale.xiaolumm.models import XiaoluMama, MamaFortune, CashOut
from flashsale.xiaolumm.models.models_fortune import CarryRecord, OrderCarry, AwardCarry, ClickCarry, \
    MAMA_FORTUNE_HISTORY_LAST_DAY

# 在下次活动前设置此处，以自动重设变更统计时间
STAT_TIME = datetime.datetime(2016, 7, 24)
# if datetime.datetime.now() < datetime.datetime(2016, 7, 28) \
# else datetime.datetime(2016, 7, 28)


class MamaCarryTotal(BaseModel):
    mama = models.OneToOneField(XiaoluMama, primary_key=True)
    history_total = models.IntegerField(default=0, verbose_name=u'历史收益总额', help_text=u'单位为分')
    stat_time = models.DateTimeField(default=STAT_TIME, verbose_name=u'统计起始时间')
    duration_total = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    history_num = models.IntegerField(default=0, db_index=True, verbose_name=u'历史订单数量')
    duration_num = models.IntegerField(default=0, verbose_name=u'活动订单数量')
    carry_records = JSONCharMyField(max_length=10240, blank=True, default='[]', verbose_name=u'每日收益关联')
    total_rank_delay = models.IntegerField(default=0, verbose_name=u'总排名', help_text=u'单位为分,每日更新，从cache中可实时更新')
    duration_rank_delay = models.IntegerField(default=0, verbose_name=u'活动期排名', help_text=u'单位为分，每日更新，从cache中可实时更新')

    class Meta:
        db_table = 'xiaolumm_carry_total'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈收益排名'
        verbose_name_plural = u'小鹿妈妈收益排名列表'

    @property
    def total(self):
        return self.history_total + self.duration_total

    @property
    def mama_nick(self):
        return self.mama.get_mama_customer().nick

    @property
    def num(self):
        return self.history_num + self.duration_num

    @property
    def thumbnail(self):
        return self.mama.get_mama_customer().thumbnail

    @property
    def mobile(self):
        return self.mama.get_mama_customer().mobile

    @property
    def phone(self):
        return self.mama.get_mama_customer().phone

    def __unicode__(self):
        return 'mama rank:%d' % (self.mama_id,)

    @staticmethod
    def __generate(mama_id):
        rank = MamaCarryTotal(mama_id=mama_id)
        rank.history_total = rank.get_history_total()
        records = CarryRecord.objects.filter(date_field__gte=STAT_TIME, mama_id=mama_id, status=CarryRecord.CONFIRMED)
        if records:
            rank.carry_records = [c.id for c in records]
            rank.duration_total = sum([c.carry_num for c in records])
            rank.history_num = OrderCarry.objects.filter(mama_id=mama_id, status=2, created__lt=STAT_TIME).count()
            rank.duration_num = OrderCarry.objects.filter(mama_id=mama_id, status=2, created__gte=STAT_TIME).count()
        rank.save()
        return rank

    @staticmethod
    def get_by_mama_id(mama_id):
        if not MamaCarryTotal.objects.filter(mama_id=mama_id).exists():
            return MamaCarryTotal.__generate(mama_id)
        return MamaCarryTotal.objects.get(mama_id=mama_id)

    def get_history_total(self):
        order_carry_sum = OrderCarry.objects.filter(mama_id=self.mama_id, created__range=(
            MAMA_FORTUNE_HISTORY_LAST_DAY, STAT_TIME)).aggregate(
            total=Sum('carry_num')).get('total') or 0
        award_carry_sum = AwardCarry.objects.filter(mama_id=self.mama_id, created__range=(
            MAMA_FORTUNE_HISTORY_LAST_DAY, STAT_TIME)).aggregate(
            total=Sum('carry_num')).get('total') or 0
        click_carry_sum = ClickCarry.objects.filter(mama_id=self.mama_id, created__range=(
            MAMA_FORTUNE_HISTORY_LAST_DAY, STAT_TIME)).aggregate(
            total=Sum('confirmed_click_price')).get('total') or 0
        fortune = MamaFortune.objects.filter(mama_id=self.mama_id).first()
        history_confirmed = fortune.history_confirmed if fortune else 0
        history_cash_out = CashOut.objects.filter(xlmm=self.mama_id, status=CashOut.COMPLETED,
                                                  approve_time__lt=MAMA_FORTUNE_HISTORY_LAST_DAY).aggregate(
            total=Sum('value')).get('total') or 0
        return order_carry_sum + award_carry_sum + click_carry_sum + history_confirmed + history_cash_out

    @staticmethod
    def stat_batch_history_total():
        """
            历史总金额为OrderCarry,AwardCarry,ClickCarry
        """
        mama_ids = [i['id']
                    for i in XiaoluMama.objects.filter(progress__in=[XiaoluMama.PAY, XiaoluMama.PASS],
                                                       status=XiaoluMama.EFFECT).values('id')]
        records = []
        for mama_id in mama_ids:
            m = MamaCarryTotal(mama_id=mama_id)
            m.history_total = m.get_history_total()
            records.append(m)
        MamaCarryTotal.objects.bulk_create(records)

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
        mama_ids = [i['id']
                    for i in XiaoluMama.objects.filter(progress__in=[XiaoluMama.PAY, XiaoluMama.PASS],
                                                       status=XiaoluMama.EFFECT).values('id')]
        exist_ids = [m['mama_id'] for m in MamaCarryTotal.objects.filter(stat_time=STAT_TIME).values('mama_id')]
        mama_ids = list(set(mama_ids) - set(exist_ids))
        #res = []
        for mama_id in mama_ids:
            m = MamaCarryTotal(mama_id=mama_id)
            m.history_total = m.get_history_total()
            records = CarryRecord.objects.filter(date_field__gte=STAT_TIME, mama_id=mama_id,
                                                 status=CarryRecord.CONFIRMED)
            m.carry_records = [c.id for c in records]
            m.duration_total = sum([c.carry_num for c in records])
            m.history_num = OrderCarry.objects.filter(mama_id=mama_id, status=2, created__lt=STAT_TIME).count()
            m.duration_num = OrderCarry.objects.filter(mama_id=mama_id, status=2, created__gte=STAT_TIME).count()
            m.save()
        #res.append(m)
        #MamaCarryTotal.objects.bulk_create(res)

    @staticmethod
    def stat_history_total(mama_id):
        """
            历史总金额为OrderCarry,AwardCarry,ClickCarry
        """
        rank = MamaCarryTotal.objects.get_or_create(mama_id=mama_id)
        rank.history_total = rank.get_history_total()
        rank.save('history_total', 'modified')

    @staticmethod
    def update_ranking(mama_id, stat_history=False):
        """
            更新数据以更新排名-其实这个方法尽可能更新了需要的数，唯独不更新排名
            排名更新在post_save事件中，15分钟以后，由celery事件更新排名。
        """
        print 'update_ranking now'
        if not MamaCarryTotal.objects.filter(mama_id=mama_id).exists():
            return MamaCarryTotal.__generate(mama_id)
        rank = MamaCarryTotal.objects.get(mama_id=mama_id)
        records = CarryRecord.objects.filter(date_field__gte=STAT_TIME, mama_id=mama_id, status=CarryRecord.CONFIRMED)
        rank.carry_records = [c.id for c in records]
        rank.duration_total = sum([c.carry_num for c in records])
        rank.history_num = OrderCarry.objects.filter(mama_id=mama_id, status=2, created__lt=STAT_TIME).count()
        rank.duration_num = OrderCarry.objects.filter(mama_id=mama_id, status=2, created__gte=STAT_TIME).count()
        if stat_history:
            history_total = rank.get_history_total()
            if rank.history_total != history_total:
                rank.history_total = history_total
        rank.save()
        return rank

    @staticmethod
    def get_ranking_list():
        return MamaCarryTotal.objects.exclude(duration_total=0).order_by('duration_total')

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
    def total_display(self):
        return float('%.2f' % (self.total * 0.01))

    @property
    def duration_total_display(self):
        return '%.2f' % (self.duration_total * 0.01)

    @staticmethod
    def get_ranking_list():
        return MamaCarryTotal.objects.order_by((F('duration_total') + F('history_total')).desc())

    @staticmethod
    def get_duration_ranking_list():
        return MamaCarryTotal.objects.order_by((F('duration_total')).desc())

    @staticmethod
    def reset_rank():
        MamaCarryTotal.batch_generate()
        i = 1
        rank = 1
        last_value = 0
        res = {}
        for m in MamaCarryTotal.objects.order_by((F('duration_total') + F('history_total')
                                                  ).desc()).values('mama_id',
                                                                   'duration_total',
                                                                   'history_total'):
            if m['duration_total'] + m['history_total'] < last_value:
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
        last_value = 0
        res = {}
        for m in MamaCarryTotal.objects.order_by((F('duration_total')).desc()).values('mama_id', 'duration_total'):
            if m['duration_total'] < last_value:
                last_value = m['duration_total']
                rank = i
            res[m['mama_id']] = rank
            i += 1
        multi_update(MamaCarryTotal, 'mama_id', 'duration_rank_delay', res)


def multi_update(model_class, key_attr, value_attr, res):
    sql_begin = 'UPDATE %s SET %s = CASE %s ' % (model_class._meta.db_table, value_attr, key_attr)
    sql_whens = ['WHEN ' + str(id) + ' THEN ' + str(res[id]) for id in res]
    sql_end = ' END'
    sql = sql_begin + ' '.join(sql_whens) + sql_end
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


def update_team_carry_total(sender, instance, created, **kwargs):
    from flashsale.xiaolumm.tasks_mama_carry_total import task_update_team_carry_total
    if datetime.datetime.now() > STAT_TIME:
        for team in instance.teams.all():
            task_update_team_carry_total.delay(team.mama_id)


post_save.connect(update_team_carry_total,
                  sender=MamaCarryTotal, dispatch_uid='post_save_carrytotal_update_team_carry_total')


class MamaTeamCarryTotal(BaseModel):
    mama = models.OneToOneField(XiaoluMama, primary_key=True)
    total = models.IntegerField(default=0, verbose_name=u'团队收益总额', help_text=u'单位为分')
    num = models.IntegerField(default=0, verbose_name=u'团队订单数量')
    duration_num = models.IntegerField(default=0, verbose_name=u'活动期间团队订单数量')
    duration_total = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    stat_time = models.DateTimeField(default=STAT_TIME, verbose_name=u'统计起始时间')
    members = models.ManyToManyField(MamaCarryTotal, related_name='teams')
    total_rank_delay = models.IntegerField(default=0, verbose_name=u'总排名', help_text=u'单位为分,每日更新，从cache中可实时更新')
    duration_rank_delay = models.IntegerField(default=0, verbose_name=u'活动期排名', help_text=u'单位为分，每日更新，从cache中可实时更新')

    # mama_ids = JSONCharMyField(max_length=10240, blank=True, default='[]', verbose_name=u'相关妈妈')

    class Meta:
        db_table = 'xiaolumm_team_carry_total'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈团队收益排名'
        verbose_name_plural = u'小鹿妈妈团队收益排名列表'

    def __unicode__(self):
        return 'mama rank:%d' % (self.mama_id,)

    @property
    def mama_nick(self):
        return self.mama.get_mama_customer().nick

    @property
    def thumbnail(self):
        return self.mama.get_mama_customer().thumbnail

    @property
    def mobile(self):
        return self.mama.get_mama_customer().mobile

    @property
    def phone(self):
        return self.mama.get_mama_customer().phone

    @property
    def rank(self):
        if not hasattr(self, '_rank_'):
            return 0
        return self._rank_

    @property
    def mama_ids(self):
        if not hasattr(self, '_mama_ids'):
            self._mama_ids_ = MamaTeamCarryTotal.get_team_ids(self.mama_id)
            # self._mama_ids_ = [m['mama_id'] for m in self.members.values('mama_id')]
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

    @staticmethod
    def get_by_mama_id(mama_id):
        if not MamaTeamCarryTotal.objects.filter(mama_id=mama_id).exists():
            return MamaTeamCarryTotal.generate(mama_id)
        return MamaTeamCarryTotal.objects.filter(mama_id=mama_id).first()

    @staticmethod
    def generate(mama_id):
        mama_ids = MamaTeamCarryTotal.get_team_ids(mama_id)
        m = MamaTeamCarryTotal(
            mama_id=mama_id,
        )
        m.restat(mama_ids)
        m.save()
        for mama in MamaCarryTotal.objects.filter(mama_id__in=mama_ids):
            m.members.add(mama)
        m.save()
        return m

    @staticmethod
    def batch_generate():
        MamaCarryTotal.batch_generate()
        mids = [m['mama_id'] for m in MamaCarryTotal.objects.values('mama_id')]
        for mama_id in mids:
            MamaTeamCarryTotal.generate(mama_id)

    def restat(self, mama_ids):
        res = MamaCarryTotal.objects.filter(mama_id__in=mama_ids).aggregate(
            total=Sum('history_total') + Sum('duration_total'),
            duration_total=Sum('duration_total'),
            num=Sum('history_num') + Sum('duration_num'),
            duration_num=Sum('duration_num')
        )
        self.total = res.get('total') or 0
        self.duration_total = res.get('duration_total') or 0
        self.num = res.get('num') or 0
        self.duration_num = res.get('duration_num') or 0

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
        return MamaTeamCarryTotal.objects.order_by((F('total')).desc())

    @staticmethod
    def get_duration_ranking_list():
        return MamaTeamCarryTotal.objects.order_by((F('duration_total')).desc())


    @staticmethod
    def reset_rank():
        MamaTeamCarryTotal.batch_generate()
        i = 1
        rank = 1
        last_value = 0
        res = {}
        for m in MamaTeamCarryTotal.objects.order_by((F('total')).desc()).values('mama_id', 'total'):
            if m['total'] < last_value:
                last_value = m['total']
                rank = i
            res[m['mama_id']] = rank
            i += 1
        multi_update(MamaTeamCarryTotal, 'mama_id', 'total_rank', res)

    @staticmethod
    def reset_rank_duration():
        MamaTeamCarryTotal.batch_generate()
        i = 1
        rank = 1
        last_value = 0
        res = {}
        for m in MamaTeamCarryTotal.objects.order_by((F('duration_total')).desc()).values('mama_id', 'duration_total'):
            if m['duration_total'] < last_value:
                last_value = m['duration_total']
                rank = i
            res[m['mama_id']] = rank
            i += 1
        multi_update(MamaTeamCarryTotal, 'mama_id', 'duration_rank', res)


class CarryTotalRecord(BaseModel):
    """
        活动记录
    """
    mama = models.ForeignKey(XiaoluMama)
    stat_time = models.DateTimeField(verbose_name=u'统计时间')
    total_rank = models.IntegerField(default=0, verbose_name=u'总额排名')
    duration_rank = models.IntegerField(default=0, verbose_name=u'活动期间排名')
    history_total = models.IntegerField(default=0, verbose_name=u'历史收益总额', help_text=u'单位为分')
    duration_total = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    history_num = models.IntegerField(default=0, db_index=True, verbose_name=u'团队订单数量')
    duration_num = models.IntegerField(default=0, verbose_name=u'活动期间团队订单数量')
    carry_records = JSONCharMyField(max_length=10240, blank=True, default='[]', verbose_name=u'每日收益关联')

    class Meta:
        db_table = 'xiaolumm_carry_total_record'
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈收益排名记录'
        verbose_name_plural = u'小鹿妈妈收益排名记录'

    @staticmethod
    def create(carry_total, save=True):
        record = CarryTotalRecord(
            mama_id=carry_total.mama_id,
            stat_time=carry_total.stat_time,
            total_rank=carry_total.total_rank,
            duration_rank=carry_total.duration_rank,
            history_total=carry_total.history_total,
            duration_total=carry_total.duration_total,
            history_num=carry_total.history_num,
            duration_num=carry_total.duration_num,
            carry_records=carry_total.carry_records,
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
                duration_total=m.duration_total
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


class TeamCarryTotalRecord(BaseModel):
    """
        活动记录
    """
    mama = models.ForeignKey(XiaoluMama)
    stat_time = models.DateTimeField(default=STAT_TIME, verbose_name=u'统计起始时间')
    total_rank = models.IntegerField(default=0, verbose_name=u'总额排名')
    duration_rank = models.IntegerField(default=0, verbose_name=u'活动期间排名')
    total = models.IntegerField(default=0, verbose_name=u'团队收益总额', help_text=u'单位为分')
    duration_total = models.IntegerField(default=0, verbose_name=u'统计期间收益总额', help_text=u'单位为分')
    num = models.IntegerField(default=0, db_index=True, verbose_name=u'团队订单数量')
    duration_num = models.IntegerField(default=0, verbose_name=u'活动期间团队订单数量')
    mama_ids = JSONCharMyField(max_length=10240, blank=True, default='[]', verbose_name=u'相关妈妈')

    class Meta:
        db_table = 'xiaolumm_team_carry_total_record'
        app_label = 'xiaolumm'
        verbose_name = u'妈妈团队收益排名记录'
        verbose_name_plural = u'妈妈团队收益排名记录'
