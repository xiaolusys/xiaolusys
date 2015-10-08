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
import logging
import datetime
from shopback.base import log_action, ADDITION, CHANGE
from tasks import calcu_refund_info_by_pro

logger = logging.getLogger('django.request')

from shopback.items.models import Product
from supplychain.supplier.models import SaleProduct
from flashsale.dinghuo.models import RGDetail, ReturnGoods


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
        return "", 0, "", ""


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
                task_id = calcu_refund_info_by_pro.s(pro_queryset=pro)()
                return Response({"task_id": task_id})

        date_from = (content.get('date_from', None))
        date_to = (content.get('date_to', None))

        date_from, date_to = time_zone_handler(date_from, date_to)
        # 过滤 时间段中　上架时间　　的所有产品
        tz_pros = Product.objects.filter(sale_time__gte=date_from, sale_time__lte=date_to)
        task_id = calcu_refund_info_by_pro.s(pro_queryset=tz_pros)()
        return Response({"task_id": task_id})

    def post(self, request, format=None):
        content = request.REQUEST
        arr = content.get("arr", None)
        data = eval(arr)  # json字符串转化
        print data
        return_num = 0
        sum_amount = 0.0
        rg = ReturnGoods()
        supplier = data[0]['supplier']
        pro_id = data[0]['pro_id']
        rg.product_id = pro_id
        rg.supplier_id = supplier
        rg.save()
        for i in data:
            sku_return_num = int(i['return_num'])
            price = float(i['price'])
            sku_id = int(i['sku_id'])
            inferior_num = int(i['sku_inferior_num'])
            return_num = return_num + sku_return_num  # 累计产品的退货数量
            sum_amount = sum_amount + price * sku_return_num
            rg_d = RGDetail.objects.create(skuid=sku_id, return_goods_id=rg.id, num=sku_return_num,
                                           inferior_num=inferior_num, price=price)
            log_action(request.user.id, rg_d, ADDITION, u'创建退货单')

        rg.return_num = return_num
        rg.sum_amount = sum_amount
        rg.noter = request.user.username
        rg.save()
        log_action(request.user.id, rg, ADDITION, u'创建退货单')

        return Response({"res": True})
