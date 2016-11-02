# coding:utf-8
from rest_framework import generics
from shopback.categorys.models import ProductCategory
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from .tasks import task_calc_performance_by_user, task_calc_performance_by_supplier, task_calc_sale_product
import datetime
from supplychain.supplier.models import SaleCategory


class StatsPerformanceView(generics.ListCreateAPIView):
    """
        绩效统计
    """
    queryset = ProductCategory.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "xiaolumm/data2performance.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        content = request.GET
        category = content.get("category", "0")
        start_date = content.get("df", datetime.date.today().strftime("%Y-%m-%d"))
        end_date = content.get("dt", datetime.date.today().strftime("%Y-%m-%d"))
        all_category = SaleCategory.objects.filter(is_parent=True)
        start_task = task_calc_performance_by_user.delay(start_date, end_date, category)
        return Response(
            {"task_id": start_task, "category": int(category), "start_date": start_date, "end_date": end_date,
             "all_category": all_category})


class StatsSupplierView(generics.ListCreateAPIView):
    """
        供应商统计
    """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "xiaolumm/data2supplier.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        content = request.GET
        category = content.get("category", "0")
        start_date = content.get("df", datetime.date.today().strftime("%Y-%m-%d"))
        end_date = content.get("dt", datetime.date.today().strftime("%Y-%m-%d"))
        all_category = SaleCategory.objects.filter(is_parent=True)
        start_task = task_calc_performance_by_supplier.delay(start_date, end_date, category)
        return Response(
            {"task_id": start_task, "category": int(category), "start_date": start_date, "end_date": end_date,
             "all_category": all_category})


from supplychain.supplier.models import SaleCategory


class StatsSaleProdcutView(generics.ListCreateAPIView):
    """
        选款统计
    """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "xiaolumm/data2saleproduct.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        content = request.GET
        start_date = content.get("df", datetime.date.today().strftime("%Y-%m-%d"))
        end_date = content.get("dt", datetime.date.today().strftime("%Y-%m-%d"))
        start_task = task_calc_sale_product.delay(start_date, end_date)
        return Response(
            {"task_id": start_task, "start_date": start_date, "end_date": end_date})
