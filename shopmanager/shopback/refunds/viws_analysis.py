# coding=utf-8
"""
统计退款率　退货率
"""
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework import permissions
from shopback.base import log_action, ADDITION, CHANGE
from tasks import refund_analysis
from flashsale.pay.models import SaleOrder, SaleTrade
import logging
import datetime

logger = logging.getLogger('django.request')


class RefundAnaView(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "refunds/refund_anav2.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        content = request.REQUEST
        date = (content.get('date', None))
        task = refund_analysis.s(date)()
        return Response({"task_id": task.task_id})


    def post(self, request, format=None):
        content = request.REQUEST
        arr = content.get("arr", None)
        return Response({"res": True})
