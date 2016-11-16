# coding=utf-8
import datetime
from django.db.models import F, Q, Sum
from rest_framework import generics

from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response
from core.options import log_action, CHANGE
from flashsale.dinghuo.models import OrderList, OrderDetail
from shopback.items.models import Product, ProductSku
from django.db import transaction


class SetRemainNumView(generics.ListCreateAPIView):
    """
        根据订货单来生成预留数
    """
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "dinghuo/product/set_remain.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        product_outer_id = request.GET.get("search_input", "")
        orderlists = request.GET.get("orderlist", "")
        if not product_outer_id:
            return Response({"product_outer_id": product_outer_id})
        try:
            product = Product.objects.get(outer_id=product_outer_id, status=Product.NORMAL)
            all_skus = product.normal_skus
            normal_skus = []
            all_dinghuo = OrderDetail.objects.filter(product_id=product.id).exclude(
                orderlist__status=OrderList.ZUOFEI)
            for one_sku in all_skus:
                one_sku_dinghuo = all_dinghuo.filter(chichu_id=one_sku.id).aggregate(total_num=Sum('buy_quantity')).get(
                    'total_num') or 0
                normal_skus.append(
                    {"sku_id": one_sku.id, "one_sku_dinghuo": one_sku_dinghuo, "sku_name": one_sku.properties_alias})
            return Response({"product_outer_id": product_outer_id, "product": product,
                             "normal_skus": normal_skus, "all_dinghuo": all_dinghuo})
        except:
            return Response({"product_outer_id": product_outer_id})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        post = request.POST
        sku_list_str = post.get("sku_list", "")
        sku_list_str = sku_list_str[0: len(sku_list_str) - 1]
        sku_list = sku_list_str.split(",")
        for one_sku in sku_list:
            try:
                sku_bean = ProductSku.objects.get(id=one_sku)
                sku_bean.remain_num = post.get(one_sku, 0)
                sku_bean.save()
            except:
                continue
        log_action(request.user.id, sku_bean.product, CHANGE, u'修改预留数')
        return Response({"result": "OK"})
