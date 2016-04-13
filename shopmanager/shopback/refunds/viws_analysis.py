# coding=utf-8
"""
统计退款率　退货率
"""
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.forms import model_to_dict
from rest_framework.response import Response
from shopback.refunds.models_refund_rate import PayRefundRate, PayRefNumRcord

import logging
import datetime
import json

logger = logging.getLogger('django.request')


class RefundRateView(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "refunds/refund_rate_chart.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        time_from = datetime.date.today() - datetime.timedelta(days=30)
        time_to = datetime.date.today() - datetime.timedelta(days=1)
        return Response({"time_from": time_from, "time_to": time_to})

    def post(self, request, format=None):
        content = request.REQUEST
        date_from = content.get("date_from", None)
        date_to = content.get("date_to", None)
        year, montth, day = map(int, date_from.split('-'))
        time_from = datetime.datetime(year, montth, day, 0, 0, 0)
        year, montth, day = map(int, date_to.split('-'))
        time_to = datetime.datetime(year, montth, day, 23, 59, 59)
        rates = PayRefundRate.objects.filter(date_cal__gte=time_from, date_cal__lte=time_to).order_by('date_cal')
        data = []
        for rate in rates:
            rate_dic = model_to_dict(rate, fields=['date_cal', 'ref_num', "pay_num", 'ref_rate'])
            data.append(rate_dic)

        return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder),
                            content_type="application/json")


class RefundRecord(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "refunds/refund_rate_chart.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        time_from = datetime.date.today() - datetime.timedelta(days=30)
        time_to = datetime.date.today() - datetime.timedelta(days=1)
        return Response({"time_from": time_from, "time_to": time_to})

    def post(self, request, format=None):
        content = request.REQUEST
        date_from = content.get("date_from", None)
        date_to = content.get("date_to", None)
        year, month, day = map(int, date_from.split('-'))
        time_from = datetime.datetime(year, month, day, 0, 0, 0)
        year, month, day = map(int, date_to.split('-'))
        time_to = datetime.datetime(year, month, day, 23, 59, 59)
        records = PayRefNumRcord.objects.filter(date_cal__gte=time_from, date_cal__lte=time_to).order_by('date_cal')
        data = []
        for record in records:
            try:
                pay_num = PayRefundRate.objects.get(date_cal=record.date_cal).pay_num
            except PayRefundRate.DoesNotExist:
                continue
            rate_dic = model_to_dict(record, fields=['date_cal', 'ref_num_out', "ref_num_in", "ref_sed_num"])
            rate_dic['pay_num'] = pay_num
            data.append(rate_dic)
        return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder),
                            content_type="application/json")
