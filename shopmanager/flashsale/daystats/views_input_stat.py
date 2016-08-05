# *_* coding=utf-8 *_*
import datetime

from rest_framework import generics
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response

from shopback.items.models import Product
import flashsale.dinghuo.utils as tools_util


class ProductInputStatView(generics.ListCreateAPIView):
    """
        录入资料统计
    """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "xiaolumm/data2saleinput.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        content = request.GET
        start_date_str = content.get("df", datetime.date.today().strftime("%Y-%m-%d"))
        end_date_str = content.get("dt", datetime.date.today().strftime("%Y-%m-%d"))
        start_date = tools_util.parse_date(start_date_str)
        year, month, day = end_date_str.split('-')
        end_date = datetime.date(int(year), int(month), int(day))
        all_sale_charger = Product.objects.filter(created__range=(start_date, end_date), status=Product.NORMAL).values(
            "sale_charger").distinct()

        all_nv_product = Product.objects.filter(created__range=(start_date, end_date), status=Product.NORMAL,
                                                category__parent_cid=8)
        all_child_product = Product.objects.filter(created__range=(start_date, end_date), status=Product.NORMAL,
                                                   category__parent_cid=5)

        result_data = {}
        for one_sale_charger in all_sale_charger:
            temp_nv_product = all_nv_product.filter(sale_charger=one_sale_charger["sale_charger"])
            temp_child_product = all_child_product.filter(sale_charger=one_sale_charger["sale_charger"])
            result_data[one_sale_charger["sale_charger"]] = [[temp_nv_product.filter(category__cid=18).count(),
                                                              temp_nv_product.filter(category__cid=19).count(),
                                                              temp_nv_product.filter(category__cid=22).count(),
                                                              temp_nv_product.filter(category__cid=21).count(),
                                                              temp_nv_product.filter(category__cid=20).count(),
                                                              temp_nv_product.filter(category__cid=24).count()],
                                                             [temp_child_product.filter(category__cid=23).count(),
                                                              temp_child_product.filter(category__cid=17).count(),
                                                              temp_child_product.filter(category__cid=16).count(),
                                                              temp_child_product.filter(category__cid=12).count(),
                                                              temp_child_product.filter(category__cid=15).count(),
                                                              temp_child_product.filter(category__cid=14).count(),
                                                              temp_child_product.filter(category__cid=13).count(),
                                                              temp_child_product.filter(category__cid=25).count(),
                                                              temp_child_product.filter(category__cid=26).count()]]
        category_list = [u"女装/外套", u"女装/连衣", u"女装/套装", u"女装/下装", u"女装/上装", u"女装/配饰",
                         u"童装/配饰", u"童装/下装", u"童装/哈衣", u"童装/外套", u"童装/套装", u"童装/连身", u"童装/上装", u"童装/亲子", u"童装/内衣"]
        return Response({"result_data": result_data, "category_list": category_list,
                         "start_date_str": start_date_str, "end_date_str": end_date_str})


from flashsale.dinghuo.models import OrderList, OrderDetail
from django.db.models import Sum


class TempView(generics.ListCreateAPIView):
    """
        ceshi
    """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "xiaolumm/data2temp.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        content = request.GET
        supplier_name = content.get("supplier", "")
        all_product = OrderDetail.objects.filter(orderlist__supplier_shop=supplier_name).exclude(
            orderlist__status=OrderList.ZUOFEI).values("product_id").distinct()
        result_data = []
        total_money = 0
        for one_product in all_product:
            temp_list = ["", 0, 0]
            temp_product = Product.objects.get(id=one_product["product_id"])
            temp_list[0] = temp_product.name
            temp_list[1] = temp_product.cost
            buy_num = OrderDetail.objects.filter(orderlist__supplier_shop=supplier_name,
                                                 product_id=one_product["product_id"]).exclude(
                orderlist__status=OrderList.ZUOFEI).aggregate(total_num=Sum('buy_quantity')).get('total_num') or 0
            temp_list[2] = buy_num
            total_money += temp_product.cost * buy_num
            result_data.append(temp_list)

        return Response({"result_data": result_data, "supplier_name": supplier_name, "total_money": total_money})
