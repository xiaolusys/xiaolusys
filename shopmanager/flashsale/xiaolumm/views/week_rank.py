# coding=utf-8
__author__ = 'yan.huang'
from rest_framework.response import Response
from rest_framework import exceptions
from rest_framework import generics, viewsets, permissions, authentication, renderers
from rest_framework.decorators import detail_route, list_route
from django.shortcuts import get_object_or_404
from flashsale.xiaolumm.models import XiaoluMama
from flashsale.xiaolumm.models.rank import WeekMamaCarryTotal, WeekMamaTeamCarryTotal
from flashsale.xiaolumm.serializers import WeekMamaCarryTotalSerializer, WeekMamaTeamCarryTotalSerializer, \
    WeekMamaCarryTotalDurationSerializer, WeekMamaTeamCarryTotalDurationSerializer
import logging

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
        top = WeekMamaCarryTotal.get_ranking_list()[0:10]
        return Response(self.get_serializer(top, many=True).data)
        queryset = WeekMamaCarryTotal.get_ranking_list()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

    @list_route(methods=['GET'])
    def carry_duration_rank(self, request):
        top = WeekMamaCarryTotal.get_duration_ranking_list()[0:10]
        return Response(WeekMamaCarryTotalDurationSerializer(top, many=True).data)

    @detail_route(methods=['GET'])
    def get_team_members(self, request, pk):
        team = WeekMamaTeamCarryTotal.get_by_mama_id(pk)
        records = WeekMamaCarryTotal.objects.filter(mama_id__in=team.mama_ids)
        return Response(self.get_serializer(records, many=True).data)

    @list_route(methods=['GET'])
    def self_rank(self, request):
        if request.user.is_anonymous():
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        mama = request.user.customer.getXiaolumm()
        if not mama:
            raise exceptions.PermissionDenied(u'用户未登录或并非小鹿妈妈')
        mama = WeekMamaCarryTotal.objects.get(pk=mama.id)
        res = self.get_serializer(mama).data
        res['rank_add'] = 0
        res['rank'] = mama.total_rank
        return Response(res)

    def retrieve(self, request, pk):
        mama = WeekMamaCarryTotal.objects.get(pk=pk)
        res = self.get_serializer(mama).data
        res['rank_add'] = WeekMamaCarryTotal.get_rank_add(mama.id)
        res['rank'] = mama.total_rank
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
        mama = request.user.customer.getXiaolumm()
        if not mama:
            raise exceptions.ValidationError(u'用户未登录或并非小鹿妈妈')
        myteam = WeekMamaTeamCarryTotal.get_by_mama_id(mama.id)
        return Response(self.get_serializer(myteam).data)

    @list_route(methods=['GET'])
    def carry_total_rank(self, request):
        top = WeekMamaTeamCarryTotal.get_ranking_list()[0:10]
        top = list(top)
        i = 1
        for t in top:
            t._rank_ = i
            i += 1
        return Response(self.get_serializer(top, many=True).data)

    @list_route(methods=['GET'])
    def carry_duration_rank(self, request):
        top = WeekMamaTeamCarryTotal.get_duration_ranking_list()[0:100]
        top = list(top)
        i = 1
        for t in top:
            t._rank_ = i
            i += 1
        return Response(WeekMamaTeamCarryTotalDurationSerializer(top, many=True).data)

    def retrieve(self, request, pk):
        mama = get_object_or_404(XiaoluMama, pk=pk)
        res = self.get_serializer(WeekMamaTeamCarryTotal.get_by_mama_id(mama.id)).data
        res['rank_add'] = WeekMamaTeamCarryTotal.get_rank_add(pk)
        return Response(res)
