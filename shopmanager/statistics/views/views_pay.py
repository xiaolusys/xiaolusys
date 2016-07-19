# coding=utf-8
import logging
import datetime
from rest_framework import permissions, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer

from statistics.tasks import task_statistics_product_sale_num

logger = logging.getLogger(__name__)


class SaleNumberStatiticsView(APIView):
    def get(self, request):
        content = request.REQUEST
        sale_time_left = content.get("time_left") or datetime.date.today() - datetime.timedelta(days=15)
        sale_time_right = content.get("time_right") or datetime.date.today()
        category = content.get("category") or None
        task_id = task_statistics_product_sale_num.delay(sale_time_left, sale_time_right, category)
        return Response({"code": 0, "task_id": str(task_id)})
