# -*- coding:utf-8 -*-
import datetime
from django.db import models
from django.db.models import Sum
from core.models import BaseModel
from core.fields import JSONCharMyField
from flashsale.xiaolumm.models.models_fortune import MamaDailyAppVisit
from flashsale.xiaolumm.models import CashOut, XiaoluMama
from flashsale.pay.models import SaleTrade
from flashsale.xiaolumm.models.models_fortune import ReferalRelationship
import logging

logger = logging.getLogger('django.request')
ROI_CLICK_START = datetime.date(2015, 8, 25)
ORDER_RATEUP_START = datetime.date(2015, 7, 8)
ORDER_REBETA_START = datetime.datetime(2015, 6, 19)

MM_CLICK_DAY_LIMIT = 1
MM_CLICK_DAY_BASE_COUNT = 10
MM_CLICK_PER_ORDER_PLUS_COUNT = 50


class XlmmEffectScore(BaseModel):
    mama_id = models.IntegerField(null=True, db_index=True)
    score = models.IntegerField(default=0, verbose_name=u'评分')
    stat_time = models.DateTimeField(verbose_name=u'统计时间')

    class Meta:
        unique_together = ('mama_id', 'stat_time')
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈真实性个人评分'
        verbose_name_plural = u'小鹿妈妈真实性个人评分列表'

    @staticmethod
    def generate(mama_dict, stat_time=None):
        if type(mama_dict) is list:
            mama_dict = XiaoluMama.get_customer_dict(mama_dict)
        if not stat_time:
            stat_time = datetime.datetime.now()
        res = XlmmEffectScore.get_scores(mama_dict)
        scores = []
        for mama_id in mama_dict:
            x = XlmmEffectScore(
                mama_id=mama_id,
                score=res.get(mama_id, 0),
                stat_time=stat_time
            )
            scores.append(x)
        XlmmEffectScore.objects.bulk_create(scores)

    @staticmethod
    def get_scores(mama_dict):
        mama_ids = mama_dict.keys()
        res = {}
        mids = MamaDailyAppVisit.objects.filter(mama_id__in=mama_ids).values_list('mama_id', flat=True)
        cashout_mids = CashOut.objects.filter(xlmm__in=mama_ids).values_list('xlmm', flat=True)
        st_cids = SaleTrade.objects.filter(buyer_id__in=mama_dict.values()).values_list('buyer_id', flat=True)
        ma_mids = ReferalRelationship.objects.filter(referal_from_grandma_id__in=mama_ids).\
            values_list('referal_from_grandma_id', flat=True)
        for mama_id in mama_ids:
            res[mama_id] = res.get(mama_id, 0) + 2 * int(mama_id in mids)
            res[mama_id] = res.get(mama_id, 0) + 3 * int(mama_id in cashout_mids)
            res[mama_id] = res.get(mama_id, 0) + 10 * int(mama_dict[mama_id] in st_cids)
            res[mama_id] = res.get(mama_id, 0) + 5 * int(mama_dict[mama_id] in ma_mids)
        return res

    @staticmethod
    def batch_generate(stat_time=None):
        if not stat_time:
            stat_time = datetime.datetime.now()
        # condition = {'charge_status': XiaoluMama.CHARGED, 'status': XiaoluMama.EFFECT,
        #                                       'progress__in': [XiaoluMama.PAY, XiaoluMama.PASS]}
        condition = {}
        mama_dict = XiaoluMama.get_customer_dict(condition)

        mama_list = mama_dict.items()
        page = 0
        limit = 5000
        now_mama_list = mama_list[page * limit: page * limit + limit]
        while now_mama_list:
            mama_dict = dict(now_mama_list)
            XlmmEffectScore.generate(mama_dict, stat_time)
            print 'XlmmEffectScore success:%d' % (page,)
            page = page + 1
            now_mama_list = mama_list[page * limit: page * limit + limit]


class XlmmTeamEffScore(BaseModel):
    mama_id = models.IntegerField(null=True, db_index=True)
    member_ids = JSONCharMyField(max_length=5120, default={}, blank=True, verbose_name=u'活动数据')
    score = models.IntegerField(default=0, verbose_name=u'评分')
    stat_time = models.DateTimeField(verbose_name=u'统计时间')

    class Meta:
        unique_together = ('mama_id', 'stat_time')
        app_label = 'xiaolumm'
        verbose_name = u'小鹿妈妈真实性团队评分'
        verbose_name_plural = u'小鹿妈妈真实性团队评分列表'

    @staticmethod
    def generate(mama_ids, stat_time=None):
        if not stat_time:
            stat_time = datetime.datetime.now()
        mama_dict = ReferalRelationship.get_referal_dict(mama_ids)
        xres = {x.id: x for x in XlmmEffectScore.objects.all()}
        scores = []
        for mama_id in mama_dict:
            x = XlmmTeamEffScore(
                mama_id=mama_id,
                member_ids=mama_dict[mama_id],
                #score=XlmmEffectScore.objects.filter(mama_id__in=mama_dict.get(mama_id, [])).aggregate(t=Sum('score')).get('t') or 0,
                score=sum([xres[id].score for id in mama_dict[mama_id] if id in xres]) if mama_dict[mama_id] else 0,
                stat_time=stat_time
            )
            scores.append(x)
        XlmmTeamEffScore.objects.bulk_create(scores)

    @staticmethod
    def batch_generate(stat_time=None):
        if not stat_time:
            stat_time = datetime.datetime.now()
        condition = {}
        # mama_ids = XiaoluMama.objects.filter(**condition).values_list('id',flat=True)
        mama_ids = XlmmEffectScore.objects.values_list('mama_id', flat=True)
        XlmmTeamEffScore.generate(mama_ids, stat_time)