# coding=utf-8
"""
统计一段时期内特卖商品的退货数量，及库存数量，并可创建退货单，退回给供应商
库存：shopback items models Product collect_num: 库存数
退货：flashsale dinghuo models_stats SupplyChainStatsOrder refund_num :退货数量 ,该产品的昨天的退货数量
"""
from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework import permissions
from django.shortcuts import redirect, get_object_or_404
from django.forms import model_to_dict
from django.db.models import Sum
import logging
import datetime
from shopback.base import log_action, ADDITION, CHANGE

logger = logging.getLogger('django.request')

from shopback.items.models import Product
from flashsale.dinghuo.models_stats import DailySupplyChainStatsOrder, SupplyChainStatsOrder
from supplychain.supplier.models import SaleProduct
from .models import ReturnGoods


def time_zone_handler(date_from=None, date_to=None):
    if date_to is None or date_to == "":
        date_to = datetime.datetime.today()
    if date_from is None or date_from == "":
        date_from = datetime.datetime.today() - datetime.timedelta(days=7)
    if type(date_to) is str and type(date_from) is str:
        time_t = date_to.split('-')
        time_f = date_from.split('-')
        tyear, tmonth, tday = time_t
        fyear, fmonth, fday = time_f
        date_from = datetime.datetime(int(tyear), int(tmonth), int(tday), 0, 0, 0)
        date_to = datetime.datetime(int(fyear), int(fmonth), int(fday), 23, 59, 59)
    return date_from, date_to


def get_sale_product(sale_product):
    """　找到库存商品对应的选品信息　"""
    try:
        sal_p = SaleProduct.objects.get(id=sale_product)
        return sal_p.sale_supplier.supplier_name, sal_p.sale_supplier.pk, \
               sal_p.sale_supplier.contact, sal_p.sale_supplier.mobile
    except SaleProduct.DoesNotExist:
        return None


class StatisRefundSupView(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "tuihuo/tuihuo_statistic.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        content = request.REQUEST
        outer_id = (content.get('outer_id', None))
        if outer_id:
            pro = Product.objects.filter(outer_id=outer_id)
            if pro.exists():
                data = []
                for i in pro:
                    # 退款数量 return_num
                    d = DailySupplyChainStatsOrder.objects.filter(product_id=i.outer_id)
                    return_num = d.aggregate(total_num=Sum('return_num')).get('total_num') or 0
                    # 退货数量 refund_num
                    s = SupplyChainStatsOrder.objects.filter(product_id=i.outer_id)
                    refund_num = s.aggregate(total_num=Sum('refund_num')).get('total_num') or 0
                    # 找出供应商和买手
                    sale_supplier_name, sale_supplier_pk, \
                    sale_supplier_contact, sale_supplier_mobile = get_sale_product(i.sale_product)

                    prod = model_to_dict(i)
                    prod['return_num'] = return_num  # 退款数量
                    prod['refund_num'] = refund_num  # 退货数量
                    prod['sale_supplier_name'] = sale_supplier_name  # 供应商名称
                    prod['sale_supplier_pk'] = sale_supplier_pk
                    prod['sale_supplier_contact'] = sale_supplier_contact  # 联系人
                    prod['sale_supplier_mobile'] = sale_supplier_mobile  # 手机
                    data.append(prod)
                return Response({"pro": data})
        date_from = (content.get('date_from', None))
        date_to = (content.get('date_to', None))
        date_from, date_to = time_zone_handler(date_from, date_to)
        # 过滤 时间段中　上架时间　　的所有产品
        tz_pros = Product.objects.filter(sale_time__gte=date_from, sale_time__lte=date_to)
        tz_data = []
        for i in tz_pros:
            # 退款数量 return_num
            d = DailySupplyChainStatsOrder.objects.filter(product_id=i.outer_id)
            return_num = d.aggregate(total_num=Sum('return_num')).get('total_num') or 0
            if return_num == 0:  # 退款数量为0　的不做退货处理
                continue
            # 退货数量 refund_num
            s = SupplyChainStatsOrder.objects.filter(product_id=i.outer_id)
            refund_num = s.aggregate(total_num=Sum('refund_num')).get('total_num') or 0
            sale_supplier_name, sale_supplier_pk, \
            sale_supplier_contact, sale_supplier_mobile = get_sale_product(i.sale_product)
            prod = model_to_dict(i)
            prod['return_num'] = return_num  # 退款数量
            prod['refund_num'] = refund_num  # 退货数量
            prod['sale_supplier_name'] = sale_supplier_name  # 供应商名称
            prod['sale_supplier_pk'] = sale_supplier_pk
            prod['sale_supplier_contact'] = sale_supplier_contact  # 联系人
            prod['sale_supplier_mobile'] = sale_supplier_mobile  # 手机
            tz_data.append(prod)
        return Response({"pro": tz_data})

    def post(self, request, format=None):
        content = request.REQUEST
        pro_id = content.get("pro_id", None)
        suppleier_id = content.get("suppleier_id", None)
        return_num = content.get("return_num", None)
        sum_amount = content.get("sum_amount", None)
        return_memo = content.get("return_memo", None)
        return_good = ReturnGoods.objects.create(noter=request.user.username,
                                                 product_id=pro_id, supplier_id=suppleier_id,
                                                 return_num=return_num, sum_amount=sum_amount,
                                                 memo=return_memo)
        log_action(request.user.id, return_good, CHANGE, u'创建退货单')
        return Response({"res": True})
