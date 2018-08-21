# coding=utf-8
import json
from rest_framework import generics, permissions, renderers, viewsets, status as rest_status
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import exceptions
from django.shortcuts import get_object_or_404
from shopback.trades.models import PackageOrder, PackageSkuItem, TradeWuliu
from shopback.trades.serializers import PackageOrderSerializer
from shopback.trades.forms import PackageOrderEditForm
from rest_framework import  authentication
import datetime,copy
from django.http import HttpResponse
from django.shortcuts import render

class SendTimeViewSet(viewsets.GenericViewSet):
    renderer_classes = (renderers.JSONRenderer,)
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = PackageSkuItem.objects.all()

    @list_route(methods=['get'])
    def get_day_delay(self,request):
        delay_day = request.GET.get('delay_day',0)
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')
        if start_time and end_time:
            start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d")
            end_time = datetime.datetime.strptime(end_time, "%Y-%m-%d")

        deadline = (datetime.datetime.now() - datetime.timedelta(days=delay_day)).strftime("%Y-%m")
        deadline = datetime.datetime.strptime(deadline,"%Y-%m")
        delay_packageskuitem = []
        if start_time and end_time:
            delay_packageskuitem = PackageSkuItem.get_no_out_sid_by_pay_time(start_time,min(end_time,datetime.datetime.now() - datetime.timedelta(days=delay_day),end_time))
            # sent_packageskuitem = PackageSkuItem.objects.filter(weight_time__gte=start_time,
            #                                                     weight_time__lte=min(end_time,datetime.datetime.now() - datetime.timedelta(
            #                                                         days=delay_day),end_time), status='sent',type=0)
        else:
            delay_packageskuitem = PackageSkuItem.get_no_out_sid_by_pay_time(deadline,datetime.datetime.now() - datetime.timedelta(days=delay_day))

            # sent_packageskuitem = PackageSkuItem.objects.filter(weight_time__startswith=deadline,
            #                                                     weight_time__lte=datetime.datetime.now() - datetime.timedelta(
            #                                                         days=delay_day), status='sent',type=0)
        return render(request, "wuliu_analysis/sent_goods_analysis.html",
                      {'delay_packageskuitem': delay_packageskuitem})