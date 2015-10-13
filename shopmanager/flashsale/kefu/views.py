# coding:utf-8
from rest_framework import generics
from shopback.categorys.models import ProductCategory
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from flashsale.signals import signal_kefu_operate_record
from flashsale.kefu.models import KefuPerformance
import time
class AddRecordView(generics.ListCreateAPIView):
    """
        客服绩效记录
    """
    queryset = ProductCategory.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "data2operate.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        print "begin send"
        signal_kefu_operate_record.send(sender=KefuPerformance, kefu_id=57, trade_id=312, operation="review")
        print "after send"
        # content = request.GET
        # category = content.get("category", "0")
        # start_date = content.get("df", datetime.date.today().strftime("%Y-%m-%d"))
        # end_date = content.get("dt", datetime.date.today().strftime("%Y-%m-%d"))
        # all_category = SaleCategory.objects.filter(is_parent=True)
        # #start_task = task_calc_operate_data.s(start_date, end_date, category)()
        return Response("fff")
