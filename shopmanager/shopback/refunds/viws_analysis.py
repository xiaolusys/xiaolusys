# coding=utf-8
"""
统计退款率　退货率
"""
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework import permissions
from shopback.refunds.models_refund_rate import PayRefundRate
import logging
import datetime
from django.http import HttpResponse
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.forms import model_to_dict

logger = logging.getLogger('django.request')


class RefundRateView(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "refunds/refund_rate_chart.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return Response()

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
                            mimetype="application/json")
