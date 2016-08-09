# coding=utf-8
import re
from django.db import models
from django.db.models import F
from rest_framework import generics, permissions, renderers, viewsets
from flashsale.xiaolumm.models import XiaoluMama, MamaFortune, PotentialMama
from rest_framework import generics, permissions, renderers, viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from flashsale.xiaolumm.models.carry_total import MamaCarryTotal, MamaTeamCarryTotal
import logging
logger = logging.getLogger(__name__)


class PotentialMamaAwardViewset(viewsets.GenericViewSet):
    renderer_classes = (renderers.JSONRenderer,)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = PotentialMama.objects.all()

    @list_route(methods=['GET'])
    def get_invite_award(self, request):
        data = {
            20: 20,
            50: 80,
            100: 200,
            200: 500
        }
        get_award = lambda x: max([data[key] for key in data if key < x])
        res = []
        for m in MamaFortune.objects.filter(invite_trial_num__gt=20):
            item = {
                'mama_id':m.mama_id,
                'invite_trial_num': m.invite_trial_num,
                'award':get_award(m.invite_trial_num),
                'mama_nick': m.xlmm.nick,
                'thumbnail': m.xlmm.thumbnail
            }
            res.append(item)
        return Response(res)

    @list_route(methods=['GET'])
    def get_income_award(self, request):
        data = {
            200 * 100: 20,
            500 * 100: 60,
            1000 * 100: 140,
            2000 * 100: 320,
            5000 * 100: 900,
            10000 * 100: 2000,
        }
        get_max = lambda l: max(l) if l else 0
        get_award = lambda x: get_max([data[key] for key in data if key < x])
        res = []
        for m in MamaCarryTotal.objects.filter(agencylevel__gt=XiaoluMama.INNER_LEVEL,
                                               last_renew_type=XiaoluMama.TRIAL, duration_total__gt=20000-F('expect_total')).order_by(
            (F('duration_total') + F('expect_total')).desc()):
            try:
                item = {
                    'mama_id': m.mama_id,
                    'income': m.duration_total + m.expect_total,
                    'award': get_award(m.duration_total + m.expect_total),
                    'mama_nick': m.mama_nick,
                    'thumbnail': m.thumbnail
                }
                res.append(item)
            except Exception, e:
                logger.error('mama no customer' + str(m.mama_id) + '|' + str(e.message))
        return Response(res)

    @list_route(methods=['GET'])
    def get_top50_award(self, request):
        res = []
        for m in MamaCarryTotal.get_activity_ranking_list()[:50]:
            try:
                item = {
                    'mama_id': m.mama_id,
                    'income': m.duration_total + m.expect_total,
                    'mama_nick': m.mama_nick,
                    'thumbnail': m.thumbnail
                }
                res.append(item)
            except Exception, e:
                logger.error('mama no customer' + str(m.mama_id) + '|' + str(e.message))
        return Response(res)

    @list_route(methods=['GET'])
    def get_team_award(self, request):
        res = []
        for m in MamaTeamCarryTotal.get_activity_ranking_list()[:50]:
            try:
                item = {
                    'mama_id': m.mama_id,
                    'income': m.expect_total,
                    'mama_nick': m.mama_nick,
                    'thumbnail': m.thumbnail
                }
                res.append(item)
            except Exception, e:
                logger.error('mama no customer' + str(m.mama_id) + '|' + str(e.message))
        return Response(res)
