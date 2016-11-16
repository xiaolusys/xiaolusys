# coding=utf-8
from rest_framework import generics
from shopback.categorys.models import ProductCategory
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from .tasks import task_calc_operate_data
import datetime
from supplychain.supplier.models import SaleCategory


class StatsDataView(generics.ListCreateAPIView):
    """
        运营数据统计
    """
    queryset = ProductCategory.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "xiaolumm/data2operate.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        content = request.GET
        category = content.get("category", "0")
        start_date = content.get("df", datetime.date.today().strftime("%Y-%m-%d"))
        end_date = content.get("dt", datetime.date.today().strftime("%Y-%m-%d"))
        all_category = SaleCategory.objects.filter(is_parent=True)
        start_task = task_calc_operate_data.delay(start_date, end_date, category)
        return Response(
            {"task_id": start_task, "category": int(category), "start_date": start_date, "end_date": end_date,
             "all_category": all_category})


from shopback.items.models import Product


class DailyCheckView(generics.ListCreateAPIView):
    """
        运营检查上架情况
    """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "xiaolumm/checkshelf.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        shelf_product = Product.objects.filter(status=Product.NORMAL, shelf_status=Product.UP_SHELF)
        all_time = shelf_product.values("sale_time").distinct()
        all_shelf_num = shelf_product.count()
        result_data = []
        for one_sale_time in all_time:
            temp_pro = Product.objects.filter(status=Product.NORMAL, sale_time=one_sale_time["sale_time"])
            all_pro_num = temp_pro.count()
            shelf_num = temp_pro.filter(shelf_status=Product.UP_SHELF).count()
            down_shelf_num = temp_pro.filter(shelf_status=Product.DOWN_SHELF).count()
            result_data.append(
                {"sale_time": one_sale_time["sale_time"].strftime('%Y-%m-%d') if one_sale_time["sale_time"] else "null",
                 "all_pro_num": all_pro_num, "shelf_num": shelf_num, "down_shelf_num": down_shelf_num})
        return Response({"result_data": result_data, "all_shelf_num": all_shelf_num})


from supplychain.supplier.models import SaleSupplier, SaleProduct


class SupplierPreviewView(generics.ListCreateAPIView):
    """
        供应商预览界面
    """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "xiaolumm/data2supplier_preview.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        content = request.GET
        supplier_name = content.get("supplier", "")
        try:
            one_supplier = SaleSupplier.objects.get(supplier_name=supplier_name)
            all_sale_product = SaleProduct.objects.filter(sale_supplier=one_supplier).exclude(
                status=SaleProduct.IGNORED)
            sale_product_ids = [one_saleproduct.id for one_saleproduct in all_sale_product]
            all_product = Product.objects.filter(sale_product__in=sale_product_ids)
        except:
            return Response()
        return Response({"all_product": all_product, "supplier_name": supplier_name})
