# coding=utf-8
import json
import datetime
from django.shortcuts import get_object_or_404
from django.forms import model_to_dict
from rest_framework.decorators import detail_route, list_route
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from flashsale.pay.serializers.teambuy import TeamBuySerializer
from flashsale.pay.models import TeamBuy, TeamBuyDetail, Customer


class TeamBuyViewSet(viewsets.GenericViewSet, viewsets.mixins.RetrieveModelMixin):
    queryset = TeamBuy.objects.all()
    serializer_class = TeamBuySerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    @detail_route(methods=['GET'])
    def team_info(self, request, pk):
        try:
            teambuy = TeamBuy.objects.filter(pk=pk).first()
        except:
            teambuy = None
        if not teambuy:
            detail = get_object_or_404(TeamBuyDetail, tid=pk)
            teambuy = detail.teambuy
        return Response(self.get_serializer(teambuy).data)

    @detail_route(methods=['GET'])
    def get_share_params(self, request, pk):

        """ 获取活动分享参数 """
        active_obj = self.get_object()

        params = {}
        # if active_obj.login_required:
        if request.user and request.user.is_authenticated():
            customer = get_object_or_404(Customer, user=request.user.id)
            params.update({'customer': customer})
            mama = customer.get_charged_mama()
            if mama:
                params.update({'mama_id': mama.id})
            else:
                params.update({'mama_id': 1})
        if not params:
            params.update({'customer': {},'mama_id': 1})

        share_params = active_obj.get_shareparams(**params)
        share_params.update(qrcode_link=active_obj.get_qrcode_page_link(**params))
        return Response(share_params)