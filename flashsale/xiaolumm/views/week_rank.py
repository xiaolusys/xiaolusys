# coding=utf-8
__author__ = 'yan.huang'
import datetime
from rest_framework.response import Response
from core import xlmm_rest_exceptions
from rest_framework import exceptions
from core.xlmm_response import make_response
from rest_framework import generics, viewsets, permissions, authentication, renderers
from rest_framework.decorators import detail_route, list_route
from django.shortcuts import get_object_or_404
from flashsale.xiaolumm.models import XiaoluMama, MamaFortune
from flashsale.xiaolumm.models.rank import WeekRank, WeekMamaCarryTotal, WeekMamaTeamCarryTotal
from flashsale.xiaolumm.models.carry_total import MamaTeamCarryTotal, MamaCarryTotal
from flashsale.xiaolumm.models.carry_total import RankActivity, ActivityMamaTeamCarryTotal, ActivityMamaCarryTotal
from flashsale.xiaolumm.serializers.rank import WeekMamaCarryTotalSerializer, WeekMamaTeamCarryTotalSerializer, \
    WeekMamaCarryTotalDurationSerializer, WeekMamaTeamCarryTotalDurationSerializer
import logging
from flashsale.xiaolumm.serializers import MamaCarryTotalSerializer, ActivityMamaCarryTotalSerializer,\
    MamaTeamCarryTotalSerializer, ActivityMamaTeamCarryTotalSerializer, MamaCarryTotalDurationSerializer, \
    MamaTeamCarryTotalDurationSerializer
log = logging.getLogger('django.request')


class WeekMamaCarryTotalViewSet(viewsets.GenericViewSet, viewsets.mixins.RetrieveModelMixin,
                                viewsets.mixins.ListModelMixin):
    """
        妈妈收益排行榜
    """
    queryset = WeekMamaCarryTotal.objects.all()
    serializer_class = WeekMamaCarryTotalSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @list_route(methods=['GET'])
    def carry_total_rank(self, request):
        stat_time = request.GET.get('stat_time')
        if stat_time:
            try:
                stat_time = datetime.datetime.strptime(stat_time, '%Y%m%d')
            except:
                raise exceptions.ValidationError(make_response(u'提供的统计时间不正确'))
        top = WeekMamaCarryTotal.get_ranking_list(stat_time)[0:10]
        return Response(self.get_serializer(top, many=True).data)
        queryset = WeekMamaCarryTotal.get_ranking_list()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @list_route(methods=['GET'])
    def carry_duration_rank(self, request):
        stat_time = request.GET.get('stat_time')
        if stat_time:
            try:
                stat_time = datetime.datetime.strptime(stat_time, '%Y%m%d')
            except:
                raise exceptions.ValidationError(make_response(u'提供的统计时间不正确'))
        top = WeekMamaCarryTotal.get_duration_ranking_list(stat_time)[0:10]
        return Response(WeekMamaCarryTotalDurationSerializer(top, many=True).data)

    @detail_route(methods=['GET'])
    def get_team_members(self, request, pk):
        stat_time = request.GET.get('stat_time')
        if stat_time:
            try:
                stat_time = datetime.datetime.strptime(stat_time, '%Y%m%d')
            except:
                raise exceptions.ValidationError(make_response(u'提供的统计时间不正确'))
        stat_time = stat_time if WeekRank.check_week_begin(stat_time) else WeekRank.this_week_time()
        team = WeekMamaTeamCarryTotal.get_by_mama_id(pk, stat_time)
        if not team:
            raise exceptions.ValidationError(make_response(u'用户尚未参与团队排名统计'))
        else:
            records = WeekMamaCarryTotal.objects.filter(mama_id__in=team.mama_ids, stat_time=stat_time)
            return Response(self.get_serializer(records, many=True).data)

    @list_route(methods=['GET'])
    def self_rank(self, request):
        if request.user.is_anonymous():
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        mama = request.user.customer.get_xiaolumm()
        if not mama:
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        stat_time = request.GET.get('stat_time')
        if stat_time:
            try:
                stat_time = datetime.datetime.strptime(stat_time, '%Y%m%d')
            except:
                raise exceptions.ValidationError(make_response(u'提供的统计时间不正确'))
        if not stat_time:
            stat_time = WeekRank.this_week_time()
        wmama = WeekMamaCarryTotal.objects.filter(mama_id=mama.id, stat_time=stat_time).first()
        if not wmama:
            res = {'mama':mama.id, 'mama_nick': mama.nick, 'thumbnail':mama.thumbnail, 'total':0,
                   'num': 0, 'total_display':'0', 'rank':0}
            return Response(res)
        res = self.get_serializer(wmama).data
        res['rank_add'] = 0
        res['rank'] = wmama.total_rank
        return Response(res)

    def retrieve(self, request, pk):
        mama = get_object_or_404(WeekMamaCarryTotal, mama_id=pk)
        res = self.get_serializer(mama).data
        res['rank_add'] = 0
        res['rank'] = mama.total_rank
        return Response(res)
    #-------------------------------------------仅仅为了以前的排名页面不要挂掉----------------------------

    @detail_route(methods=['GET'])
    def activity(self, request, pk):
        res = ActivityMamaCarryTotalSerializer(MamaCarryTotal.objects.get(pk=pk)).data
        return Response(res)

    @list_route(methods=['GET'])
    def activity_carry_total_rank(self, request):
        top = MamaCarryTotal.get_activity_ranking_list()[0:100]
        res = ActivityMamaCarryTotalSerializer(top, many=True).data
        # 前台html已经提交了 只好适应一下补两句代码
        top = list(top)
        for t in top:
            res[top.index(t)]['rank'] = t.activite_rank
            res[top.index(t)]['duration_num'] = t.duration_num + t.expect_num
            res[top.index(t)]['duration_total'] = t.duration_total + t.expect_total
            res[top.index(t)]['duration_total_display'] = float('%.2f' % (res[top.index(t)]['duration_total'] * 0.01))
        return Response(res)

    @list_route(methods=['GET'])
    def activity_self_rank(self, request):
        if request.user.is_anonymous():
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        mama = request.user.customer.getXiaolumm()
        if not mama:
            raise exceptions.ValidationError(u'用户未登录或并非小鹿妈妈')
        mama_carry = MamaCarryTotal.objects.get(pk=mama.id)
        res = ActivityMamaCarryTotalSerializer(mama_carry).data
        res['rank'] = mama_carry.activite_rank
        res['rank_add'] = 0
        team = MamaTeamCarryTotal.objects.get(pk=mama_carry.mama_id)
        res['recommended_quantity'] = len(mama.get_invite_potential_mama_ids())
        res['team_total'] = team.expect_total
        res['team_rank'] = team.activite_rank
        res['team_total_display'] = float('%.2f' % (team.expect_total * 0.01))
        res['duration_total'] = mama_carry.duration_total + mama_carry.expect_total
        res['duration_total_display'] = float('%.2f' % (mama_carry.expect_total * 0.01))
        res['team_num'] = team.duration_num
        res['activite_num'] = len(mama.get_active_invite_potential_mama_ids())
        # res['invitate_num'] = 0
        return Response(res)


class WeekMamaTeamCarryTotalViewSet(viewsets.GenericViewSet, viewsets.mixins.RetrieveModelMixin,
                                    viewsets.mixins.ListModelMixin):
    """
        妈妈团队收益排行榜
    """
    queryset = WeekMamaTeamCarryTotal.objects.all()
    serializer_class = WeekMamaTeamCarryTotalSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @list_route(methods=['GET'])
    def self_rank(self, request):
        if request.user.is_anonymous():
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        mama = request.user.customer.get_xiaolumm()
        if not mama:
            raise exceptions.ValidationError(u'用户未登录或并非小鹿妈妈')
        stat_time = request.GET.get('stat_time')
        if stat_time:
            try:
                stat_time = datetime.datetime.strptime(stat_time, '%Y%m%d')
            except:
                raise exceptions.ValidationError(make_response(u'提供的统计时间不正确'))
        myteam = WeekMamaTeamCarryTotal.get_by_mama_id(mama.id, stat_time)
        if not myteam:
            res = {'mama':mama.id, 'mama_nick': mama.nick, 'thumbnail':mama.thumbnail, 'total':0,
                   'num': 0, 'total_display':'0', 'rank':0}
            return Response(res)
        return Response(self.get_serializer(myteam).data)


    @list_route(methods=['GET'])
    def carry_total_rank(self, request):
        stat_time = request.GET.get('stat_time')
        if stat_time:
            try:
                stat_time = datetime.datetime.strptime(stat_time, '%Y%m%d')
            except:
                raise exceptions.ValidationError(make_response(u'提供的统计时间不正确'))
        top = WeekMamaTeamCarryTotal.get_ranking_list(stat_time)[0:10]
        top = list(top)
        i = 1
        for t in top:
            t._rank_ = i
            i += 1
        return Response(self.get_serializer(top, many=True).data)

    @list_route(methods=['GET'])
    def carry_duration_rank(self, request):
        stat_time = request.GET.get('stat_time')
        if stat_time:
            try:
                stat_time = datetime.datetime.strptime(stat_time, '%Y%m%d')
            except:
                raise exceptions.ValidationError(make_response(u'提供的统计时间不正确'))
        top = WeekMamaTeamCarryTotal.get_duration_ranking_list(stat_time)[0:100]
        top = list(top)
        i = 1
        for t in top:
            t._rank_ = i
            i += 1
        return Response(WeekMamaTeamCarryTotalDurationSerializer(top, many=True).data)

    def retrieve(self, request, pk):
        stat_time = request.GET.get('stat_time')
        if stat_time:
            try:
                stat_time = datetime.datetime.strptime(stat_time, '%Y%m%d')
            except:
                raise exceptions.ValidationError(make_response(u'提供的统计时间不正确'))
        mama = get_object_or_404(XiaoluMama, pk=pk)
        wmm = WeekMamaTeamCarryTotal.get_by_mama_id(mama.id, stat_time)
        if not wmm:
            raise exceptions.ValidationError(make_response(u'用户未参与团队妈妈排名'))
        res = self.get_serializer(wmm).data
        res['rank_add'] = WeekMamaTeamCarryTotal.get_rank_add(pk)
        return Response(res)

    # -------------------------------------为了以前的不挂---------------------------------------------------------------------

    @list_route(methods=['GET'])
    def carry_duration_total_rank(self, request):
        top = MamaTeamCarryTotal.get_duration_ranking_list()[0:100]
        return Response(MamaTeamCarryTotalDurationSerializer(top, many=True).data)

    @detail_route(methods=['GET'])
    def activity(self, request, pk):
        res = ActivityMamaTeamCarryTotalSerializer(MamaTeamCarryTotal.get_by_mama_id(pk)).data
        return Response(res)

    @list_route(methods=['GET'])
    def activity_self_rank(self, request):
        if request.user.is_anonymous():
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        mama = request.user.customer.getXiaolumm()
        if not mama:
            raise exceptions.ValidationError(u'用户未登录或并非小鹿妈妈')
        myteam = MamaTeamCarryTotal.get_by_mama_id(mama.id)
        return Response(ActivityMamaTeamCarryTotalSerializer(myteam).data)

    @list_route(methods=['GET'])
    def activity_carry_total_rank(self, request):
        top = MamaTeamCarryTotal.get_activity_ranking_list()[0:100]
        res = ActivityMamaTeamCarryTotalSerializer(top, many=True).data
        # 前台html已经提交了 只好适应一下补两句代码
        top = list(top)
        for t in top:
            res[top.index(t)]['rank'] = t.activite_rank
            res[top.index(t)]['duration_num'] = t.expect_num
            res[top.index(t)]['duration_total'] = t.expect_total
            res[top.index(t)]['duration_total_display'] = float('%.2f' % (t.expect_total * 0.01))
        return Response(res)


class ActivityMamaCarryTotalViewSet(viewsets.GenericViewSet, viewsets.mixins.RetrieveModelMixin,
                                viewsets.mixins.ListModelMixin):
    """
        妈妈收益排行榜
    """
    queryset = ActivityMamaCarryTotal.objects.all()
    serializer_class = ActivityMamaCarryTotalSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @detail_route(methods=['GET'])
    def invitenum(self, request, pk):
        activity = RankActivity.objects.filter(id=pk).first()
        top = ActivityMamaCarryTotal.get_ranking_list(rank_activity=activity, order_field='invite_trial_num')[0:100]
        res = ActivityMamaCarryTotalSerializer(top, many=True).data
        top = list(top)
        for t in top:
            res[top.index(t)]['rank'] = t.invite_rank
            res[top.index(t)]['invite_trial_num'] = t.invite_trial_num
        return Response(res)

    def retrieve(self, request, pk):
        if request.user.is_anonymous():
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        mama = get_object_or_404(XiaoluMama, id=pk)
        if not mama:
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        activity = RankActivity.now_activity()
        rank = activity.ranks.filter(mama_id=mama.id).first()
        if not activity or not rank:
            res = {'mama': mama.id, 'mama_nick': mama.nick, 'thumbnail': mama.thumbnail, 'mobile': mama.mobile
                   }
            res['duration_total'] = 0
            res['duration_rank'] = 0
            res['invite_trial_num'] = 0
            res['invite_rank'] = 0
            res['activity_rank'] = 0
        else:
            res = self.get_serializer(rank).data
            res['duration_total'] = rank.duration_total
            res['duration_rank'] = rank.duration_rank
            res['invite_trial_num'] = rank.invite_trial_num
            res['invite_rank'] = rank.invite_rank
            res['activity_rank'] = rank.activity_rank
        return Response(res)

    @detail_route(methods=['GET'])
    def self_rank(self, request, pk):
        if request.user.is_anonymous():
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        mama = request.user.customer.getXiaolumm()
        if not mama:
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        activity = RankActivity.objects.filter(id=pk).first() or RankActivity.now_activity()
        rank = activity.ranks.filter(mama_id=mama.id).first()
        teamrank = activity.teamranks.filter(mama_id=mama.id).first()
        fortune = MamaFortune.objects.get(mama_id=mama.id)
        if not activity or not rank:
            res = {'mama': mama.id, 'mama_nick': mama.nick, 'thumbnail': mama.thumbnail, 'mobile': mama.mobile
                   }
            res['duration_total'] = 0
            res['duration_rank'] = 0
            res['invite_trial_num'] = 0
            res['invite_rank'] = 0
            res['activity_rank'] = 0
            res['team_duration_total'] = 0
            res['team_duration_rank'] = 0
        else:
            res = self.get_serializer(rank).data
            res['duration_total'] = rank.duration_total
            res['duration_rank'] = rank.duration_rank
            res['invite_trial_num'] = rank.duration_total
            res['active_trial_num'] = fortune.active_trial_num
            res['invite_rank'] = rank.invite_rank
            res['activity_rank'] = rank.activity_rank
            res['team_duration_total'] = teamrank.duration_total
            res['team_duration_rank'] = teamrank.duration_rank
        return Response(res)

    @detail_route(methods=['GET'])
    def activity_rank(self, request, pk):
        activity = RankActivity.objects.filter(id=pk).first()
        top = ActivityMamaCarryTotal.get_ranking_list(rank_activity=activity, order_field='activity_duration_total')[0:100]
        res = ActivityMamaCarryTotalSerializer(top, many=True).data
        # 前台html已经提交了 只好适应一下补两句代码
        top = list(top)
        for t in top:
            res[top.index(t)]['rank'] = t.activity_rank
            res[top.index(t)]['duration_total'] = t.duration_total
            res[top.index(t)]['duration_total_display'] = float('%.2f' % (res[top.index(t)]['duration_total'] * 0.01))
        return Response(res)

    @detail_route(methods=['GET'])
    def get_team_members(self, request, pk):
        mama = get_object_or_404(XiaoluMama, id=pk)
        records = ActivityMamaCarryTotal.objects.filter(mama_id__in=mama.get_team_member_ids())
        return Response(self.get_serializer(records, many=True).data)


class ActivityMamaTeamCarryTotalViewSet(viewsets.GenericViewSet, viewsets.mixins.RetrieveModelMixin,
                                    viewsets.mixins.ListModelMixin):
    """
        妈妈团队收益排行榜
    """
    queryset = ActivityMamaTeamCarryTotal.objects.all()
    serializer_class = ActivityMamaTeamCarryTotalSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @detail_route(methods=['GET'])
    def activity_self_rank(self, request, pk):
        if request.user.is_anonymous():
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        activity = RankActivity.objects.filter(id=pk).first() or RankActivity.now_activity()
        mama = request.user.customer.getXiaolumm()
        if not mama:
            raise exceptions.ValidationError(u'用户未登录或并非小鹿妈妈')
        myteam = ActivityMamaTeamCarryTotal.get_by_mama_id(mama.id)
        return Response(ActivityMamaTeamCarryTotalSerializer(myteam).data)

    @detail_route(methods=['GET'])
    def activity_rank(self, request, pk):
        activity = RankActivity.objects.filter(id=pk).first()
        top = ActivityMamaTeamCarryTotal.get_ranking_list(rank_activity=activity)[0:100]
        res = ActivityMamaTeamCarryTotalSerializer(top, many=True).data
        top = list(top)
        for t in top:
            res[top.index(t)]['duration_total'] = t.duration_total
            res[top.index(t)]['duration_total_display'] = float('%.2f' % (t.duration_total * 0.01))
            res[top.index(t)]['rank'] = t.duration_rank
        return Response(res)


