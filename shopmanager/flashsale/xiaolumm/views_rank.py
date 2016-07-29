# coding=utf-8
__author__ = 'yan.huang'
from rest_framework.response import Response
from rest_framework import exceptions
from rest_framework import generics, viewsets, permissions, authentication, renderers
from rest_framework.decorators import detail_route, list_route
from .models.carry_total import MamaCarryTotal, MamaTeamCarryTotal
from .serializers import *
import logging

log = logging.getLogger('django.request')


class MamaCarryTotalViewSet(viewsets.GenericViewSet, viewsets.mixins.RetrieveModelMixin,
                            viewsets.mixins.ListModelMixin):
    """
        妈妈收益排行榜
    """
    queryset = MamaCarryTotal.get_ranking_list()
    serializer_class = MamaCarryTotalSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @list_route(methods=['GET'])
    def carry_total_rank(self, request):
        top = MamaCarryTotal.get_ranking_list()[0:10]
        top = list(top)
        i = 1
        for t in top:
            t._rank_ = i
            i += 1
        return Response(self.get_serializer(top, many=True).data)

    @list_route(methods=['GET'])
    def carry_duration_rank(self, request):
        top = MamaCarryTotal.get_duration_ranking_list()[0:10]
        top = list(top)
        i = 1
        for t in top:
            t._rank_ = i
            i += 1
        return Response(self.get_serializer(top, many=True).data)

    @detail_route(methods=['GET'])
    def get_team_members(self, request, pk):
        team = MamaTeamCarryTotal.get_by_mama_id(pk)
        records = MamaCarryTotal.objects.filter(mama_id__in=team.mama_ids)
        return Response(self.get_serializer(records, many=True).data)

    @list_route(methods=['GET'])
    def self_rank(self, request):
        if request.user.is_anonymous():
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        mama = request.user.customer.getXiaolumm()
        if not mama:
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        mama = MamaCarryTotal.objects.get(pk=mama.id)
        res = self.get_serializer(mama).data
        res['rank_add'] = 0
        res['rank'] = mama.total_rank
        return Response(res)

    def retrieve(self, request, pk):
        mama = MamaCarryTotal.objects.get(pk=pk)
        res = self.get_serializer(mama).data
        res['rank_add'] = 0
        res['rank'] = mama.total_rank
        return Response(res)

    @detail_route(methods=['GET'])
    def activity(self, request, pk):
        res = ActivityMamaCarryTotalSerializer(MamaCarryTotal.objects.get(pk=pk)).data
        return Response(res)

    @list_route(methods=['GET'])
    def activity_carry_total_rank(self, request):
        top = MamaCarryTotal.get_activity_ranking_list()[0:100]
        res = ActivityMamaCarryTotalSerializer(top, many=True).data
        # 前台html已经提交了 只好适应一下补两句代码
        for t in top:
            res[top.index(t)]['duration_rank'] = t.activite_rank
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
        res['recommended_quantity'] = max(team.members.count() - 1, 0)
        res['team_total'] = team.expect_total
        res['team_num'] = team.duration_num
        res['activite_num'] = mama.get_activite_num()
        # res['invitate_num'] = 0
        return Response(res)


class MamaTeamCarryTotalViewSet(viewsets.GenericViewSet, viewsets.mixins.RetrieveModelMixin,
                                viewsets.mixins.ListModelMixin):
    """
        妈妈团队收益排行榜
    """
    queryset = MamaTeamCarryTotal.get_ranking_list()
    serializer_class = MamaTeamCarryTotalSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @list_route(methods=['GET'])
    def self_rank(self, request):
        if request.user.is_anonymous():
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        mama = request.user.customer.getXiaolumm()
        if not mama:
            raise exceptions.ValidationError(u'用户未登录或并非小鹿妈妈')
        myteam = MamaTeamCarryTotal.get_by_mama_id(mama.id)
        return Response(self.get_serializer(myteam).data)

    @list_route(methods=['GET'])
    def carry_total_rank(self, request):
        top = MamaTeamCarryTotal.get_ranking_list()[0:10]
        top = list(top)
        i = 1
        for t in top:
            t._rank_ = i
            i += 1
        return Response(self.get_serializer(top, many=True).data)

    @list_route(methods=['GET'])
    def carry_duration_total_rank(self, request):
        top = MamaTeamCarryTotal.get_duration_ranking_list()[0:100]
        top = list(top)
        i = 1
        for t in top:
            t._rank_ = i
            i += 1
        return Response(self.get_serializer(top, many=True).data)

    def retrieve(self, request, pk):
        res = self.get_serializer(MamaTeamCarryTotal.get_by_mama_id(pk)).data
        return Response(res)

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
        for t in top:
            res[top.index(t)]['duration_rank'] = t.activite_rank
        return Response(res)
