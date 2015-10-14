# coding:utf-8
from rest_framework import generics
from shopback.categorys.models import ProductCategory
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from flashsale.signals import signal_kefu_operate_record
from .tasks import task_record_kefu_performance
from flashsale.kefu.models import KefuPerformance
import datetime


class KefuRecordView(generics.ListCreateAPIView):
    """
        客服绩效查看
    """
    queryset = ProductCategory.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "data2operate.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        content = request.GET
        record_type = content.get("record_type", "0")
        start_date = content.get("df", datetime.date.today().strftime("%Y-%m-%d"))
        end_date = content.get("dt", datetime.date.today().strftime("%Y-%m-%d"))
        all_type = KefuPerformance.OPERATE_TYPE
        start_task = task_record_kefu_performance.s(start_date, end_date, record_type)()
        return Response(
            {"task_id": start_task, "record_type": record_type, "start_date": start_date, "end_date": end_date,
             "all_type": all_type})
