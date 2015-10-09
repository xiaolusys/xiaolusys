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
from tasks import calcu_refund_info_by_pro_v2

logger = logging.getLogger('django.request')

from shopback.items.models import Product
from supplychain.supplier.models import SaleProduct
from flashsale.dinghuo.models import RGDetail, ReturnGoods


def get_sale_product(sale_product):
    """　找到库存商品对应的选品信息　"""
    try:
        sal_p = SaleProduct.objects.get(id=sale_product)
        return sal_p.sale_supplier.supplier_name, sal_p.sale_supplier.pk, \
               sal_p.sale_supplier.contact, sal_p.sale_supplier.mobile
    except SaleProduct.DoesNotExist:
        return "", 0, "", ""


def modify_sku_quantity(sku_id=None):
    pass


class StatisRefundSupView(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "tuihuo/tuihuo_statistic_page.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        content = request.REQUEST
        date_from = (content.get('date_from', None))
        date_to = (content.get('date_to', None))
        task_id = calcu_refund_info_by_pro_v2.s(date_from, date_to)()
        return Response({"task_id": task_id})

    def post(self, request, format=None):
        content = request.REQUEST
        arr = content.get("arr", None)
        data = eval(arr)  # json字符串转化
        supplier_set = set()
        pro_id_set = set()
        for i in data:
            supplier_set.add(i['supplier'])
        if supplier_set.__len__() != 1:
            return Response({"res": "multi_supplier"})
        supplier = supplier_set.pop()   # 唯一供应商

        for i in data:
            pro_id_set.add(i['pro_id'])

        for pro_id in pro_id_set:
            return_num = 0
            sum_amount = 0.0
            rg = ReturnGoods()
            rg.product_id = pro_id
            rg.supplier_id = supplier
            rg.save()
            for da in data:
                if da['pro_id'] == pro_id:   # 是当前的商品
                    sku_return_num = int(da['return_num'])
                    price = float(da['price'])
                    sku_id = int(da['sku_id'])
                    inferior_num = int(da['sku_inferior_num'])
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


from django.http import HttpResponse

from shopback.items.models import Product, ProductSku
from django.db.models import F
from common.modelutils import update_model_fields


def change_duihuo_status(request):
    content = request.REQUEST
    act_str = content.get("act_str", None)
    id = content.get("id", None)
    if not (act_str and id):
        return HttpResponse(False)
    id = int(id)
    user_id = request.user.id
    rg = ReturnGoods.objects.get(id=id)
    change_status_des = u"仓库退货单状态变更为_{0}"
    if act_str == "ok":  # 审核通过
        rg.status = ReturnGoods.VERIFY_RG
        update_model_fields(rg, update_fields=['status'])
        change_product_inventory(rg, request.user.username, request.user.id)
        log_action(user_id, rg, CHANGE, change_status_des.format(rg.get_status_display()))
        # 减少库存
    elif act_str == "no":  # 作废
        rg.status = ReturnGoods.OBSOLETE_RG
        update_model_fields(rg, update_fields=['status'])
        log_action(user_id, rg, CHANGE, change_status_des.format(rg.get_status_display()))
    elif act_str == "send":  # 已经发货
        rg.status = ReturnGoods.DELIVER_RG
        update_model_fields(rg, update_fields=['status'])
        log_action(user_id, rg, CHANGE, change_status_des.format(rg.get_status_display()))
    elif act_str == "send_ok":  # 已经发货
        rg.status = ReturnGoods.SUCCEED_RG
        update_model_fields(rg, update_fields=['status'])
        log_action(user_id, rg, CHANGE, change_status_des.format(rg.get_status_display()))
    elif act_str == "send_fail":  # 已经发货
        rg.status = ReturnGoods.FAILED_RG
        update_model_fields(rg, update_fields=['status'])
        log_action(user_id, rg, CHANGE, change_status_des.format(rg.get_status_display()))
    return HttpResponse(True)


def change_product_inventory(rg, actioner, actor_id):
    """
        仓库审核通过退货单的时候减少对应商品的库存
    """
    rg.consigner = actioner
    update_model_fields(rg, update_fields=['consigner'])
    rg_details = rg.rg_details.all()
    try:
        product = Product.objects.get(id=rg.product_id)
    except Product.DoesNotExist:
        return
    for rd in rg_details:
        try:
            psk = ProductSku.objects.get(id=rd.skuid)
            acrion_invenctory_num(product, psk, rd, actor_id)
        except ProductSku.DoesNotExist:
            return


def acrion_invenctory_num(product, psk, rd, actor_id):
    # 减少库存sku的数量
    psk_quantity = psk.quantity
    if psk_quantity >= rd.num:
        psk.quantity = F("quantity") - rd.num
        update_model_fields(psk, update_fields=['quantity'])  # 更新字段方法
    else:
        psk.quantity = 0
        update_model_fields(psk, update_fields=['quantity'])  # 更新字段方法
    action_desc = u"仓库审核退货单通过->将原来库存{0}更新为{1}".format(psk_quantity, psk.quantity)
    log_action(actor_id, psk, CHANGE, action_desc)

    # 减少库存商品的数量
    product_af = Product.objects.get(id=product.id)
    pro_collect_num = product_af.collect_num  # 原来的库存数量
    if pro_collect_num >= rd.num:
        product_af.collect_num = F("collect_num") - rd.num
        update_model_fields(product_af, update_fields=['collect_num'])  # 更新字段方法
    else:
        product_af.collect_num = 0
        update_model_fields(product_af, update_fields=['collect_num'])  # 更新字段方法
    pro_action_desc = u"仓库审核退货单通过->将原来库存{0}更新为{1}".format(pro_collect_num, product_af.collect_num)
    log_action(actor_id, product_af, CHANGE, pro_action_desc)

    # 减少库存 减去次品数　
    sku_inferior_num = psk.sku_inferior_num
    if sku_inferior_num >= rd.inferior_num:
        psk.sku_inferior_num = F("sku_inferior_num") - rd.inferior_num
        update_model_fields(psk, update_fields=['sku_inferior_num'])  # 更新字段方法
    else:
        psk.sku_inferior_num = 0
        update_model_fields(psk, update_fields=['sku_inferior_num'])  # 更新字段方法
    action_desc = u"仓库审核退货单通过->将原来次品数量{0}更新为{1}".format(sku_inferior_num, psk.sku_inferior_num)
    log_action(actor_id, psk, CHANGE, action_desc)
