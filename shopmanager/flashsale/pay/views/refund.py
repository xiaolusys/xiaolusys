# -*- encoding:utf8 -*-
import datetime
from django.forms import model_to_dict
from django.db.models import Sum
from django.shortcuts import redirect, get_object_or_404

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.views import APIView

from flashsale.pay.models import SaleTrade, SaleOrder, Customer, SaleRefund
from shopback.items.models import Product, ProductDaySale
from core.options import log_action, CHANGE
from shopback.trades.models import MergeOrder, MergeTrade
from flashsale.pay.tasks import task_send_msg_for_refund, task_update_orderlist

import logging
logger = logging.getLogger(__name__)

class RefundReason(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "salerefund/refund_reason.html"

    def get(self, request):
        content = request.REQUEST
        user_name = request.user.username
        today = datetime.datetime.today()
        pro_code = content.get("pro_code", None)
        pro_id = content.get("pro_id", None)
        if pro_code:
            pros = Product.objects.filter(outer_id=pro_code, status='normal')
        elif pro_id:
            pros = Product.objects.filter(id=pro_id, status='normal')
        else:
            return Response({'today': today, "user_name": user_name})
        if len(pros) > 0:
            pro = pros[0]
        else:
            return Response({'today': today, "user_name": user_name})

        if pro.model_id == 0 or pro.model_id is None:
            sale_refunds = SaleRefund.objects.filter(item_id=pro.id)
            sale = ProductDaySale.objects.filter(product_id=pro.id)
        else:
            pro_ids = Product.objects.filter(model_id=pro.model_id).values('id').distinct()
            sale_refunds = SaleRefund.objects.filter(item_id__in=pro_ids)
            sale = ProductDaySale.objects.filter(product_id__in=pro_ids)
        sale_num = sale.aggregate(total_sale=Sum('sale_num')).get("total_sale") or 0

        reason = {}
        des = []
        pro_info = model_to_dict(pro, fields=['name', 'pic_path', 'id'])
        for ref in sale_refunds:
            if reason.has_key(ref.reason):
                reason[ref.reason] += ref.refund_num
            else:
                reason[ref.reason] = ref.refund_num
            des.append(ref.desc)
        info_base = {'today': today, "user_name": user_name, "reason": reason, "sale_num": sale_num,
                     "desc": des, 'pro_info': pro_info}
        return Response(info_base)


class RefundAnaList(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    template_name = "salerefund/pro_ref_list.html"

    def get(self, request):
        username = request.user.username
        return Response({"username": username})


def calculate_amount_flow(refund):
    """
    :arg SaleRefund instance AND SaleOrder instance
    计算退款单中的amount_flow字段内容
    """
    order = SaleOrder.objects.get(id=refund.order_id)
    sale_trade = order.sale_trade
    if sale_trade.payment <= 0:
        raise Exception(u"付款金额有误,核实后操作")
    if order.num <= 0:
        raise Exception(u"退款数量有误,核实后操作")

    amount_flow = refund.amount_flow  # 字段原始信息
    # 请求退款的数量
    refund_num = refund.refund_num
    # 支付渠道
    channel = sale_trade.channel
    refund_money = order.payment * (refund_num / float(order.num))  # 退款总金额 = 订单实付款 * (退款数量 / 订购数量)
    # 计算钱包支付金额 = 实付款 - 实付现金
    budget_pay_money = sale_trade.payment - sale_trade.pay_cash
    # 支付渠道支付金额 = 实付款 - 钱包支付金额
    channel_cash = sale_trade.payment - budget_pay_money

    # 退款单的金额 = (渠道的金额 / 实付款) * 退款金额
    buget_refund_money = budget_pay_money / sale_trade.payment * refund_money
    channel_refund_money = channel_cash / sale_trade.payment * refund_money

    # 对应支付渠道的金额
    amount_flow[channel] = "%.2f" % channel_refund_money
    amount_flow['budget'] = "%.2f" % buget_refund_money

    if sale_trade.has_budget_paid:  # 如果是有小鹿钱包参与支付
        amount_flow['desc'] = u'您的退款已退至小鹿钱包'
    else:
        channel_name = sale_trade.get_channel_display()
        amount_flow['desc'] = u'您的退款将退至%s' % channel_name
    return amount_flow


class RefundPopPageView(APIView):
    queryset = SaleRefund.objects.all()
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer,)
    template_name = "salerefund/pop_page.html"
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        content = request.REQUEST
        pk = int(content.get('pk', None))
        sale_refund = get_object_or_404(SaleRefund, pk=pk)
        strade = get_object_or_404(SaleTrade, pk=sale_refund.trade_id)
        sale_order = get_object_or_404(SaleOrder, pk=sale_refund.order_id)
        # merge_trade = get_object_or_404(MergeTrade, tid=strade.tid)
        refund_dict = model_to_dict(sale_refund)

        refund_dict['refundd_message'] = ""
        if sale_refund.is_fastrefund():  # 如果是极速退款
            refund_dict['refundd_message'] = "[1]退回小鹿钱包 %.2f 元 实付余额%.2f"%(
                sale_refund.refund_fee,
                strade.payment > 0 and (sale_refund.refund_fee / strade.payment) * (strade.payment - strade.pay_cash) or 0)
        else:
            refund_dict['refundd_message'] = "[2]退回%s %.2f元"%(strade.get_channel_display(), sale_refund.refund_fee)

        refund_dict['tid'] = strade.tid
        refund_dict['channel'] = strade.get_channel_display()
        refund_dict['pic'] = sale_order.pic_path
        refund_dict['status'] = sale_refund.get_status_display()
        refund_dict['order_status'] = sale_order.get_status_display()
        refund_dict['payment'] = sale_order.payment
        refund_dict['order_s'] = sale_order.status
        refund_dict['pay_time'] = strade.pay_time
        # refund_dict['merge_trade_status'] = merge_trade.get_status_display()
        # refund_dict['merge_sys_status'] = merge_trade.get_sys_status_display()
        # refund_dict['sys_memo'] = merge_trade.sys_memo
        refund_dict['logistics_company'] = strade.logistics_company
        refund_dict['out_sid'] = strade.out_sid
        refund_dict['logistics_time'] = strade.consign_time
        return Response({'refund': refund_dict})

    def post(self, request, format=None):
        content = request.REQUEST
        pk = int(content.get('pk', None))
        obj = get_object_or_404(SaleRefund, pk=pk)  # 退款单

        method = content.get('method', None)
        refund_feedback = content.get('refund_feedback', None)
        if refund_feedback:
            obj.feedback = refund_feedback
        if method == "save":  # 保存退款状态　和　审核意见
            refund_status = content.get('refund_status', None)
            if refund_status:
                obj.status = refund_status
            obj.save()
            log_action(request.user.id, obj, CHANGE, '保存状态信息')
        if method == "agree_product":  # 同意退货
            # 将状态修改成卖家同意退款(退货)
            obj.status = SaleRefund.REFUND_WAIT_RETURN_GOODS
            obj.save()

            # task_update_orderlist.delay(str(obj.sku_id)) #2016-09-21
            log_action(request.user.id, obj, CHANGE, '保存状态信息到－退货状态')

        if method == "agree":  # 同意退款
            # TODO 如果退货仓库确认接受且可以二次销售，则直接退款（是否要求退运费），如果不能二次销售则需人工审核
            try:
                if obj.status in (SaleRefund.REFUND_WAIT_SELLER_AGREE,
                                  SaleRefund.REFUND_WAIT_RETURN_GOODS,
                                  SaleRefund.REFUND_CONFIRM_GOODS):
                    strade = SaleTrade.objects.get(id=obj.trade_id)
                    sorder = SaleOrder.objects.get(id=obj.order_id)
                    customer = Customer.objects.get(id=strade.buyer_id)
                    if strade.channel == SaleTrade.WALLET:
                        obj.refund_wallet_approve()

                    elif obj.is_fastrefund():
                        obj.refund_fast_approve()

                    elif obj.refund_fee > 0 and obj.charge:  # 有支付编号
                        obj.refund_charge_approve()

                    log_action(request.user.id, obj, CHANGE, u'退款审核通过:%s' % obj.refund_id)
                    # obj.amount_flow = calculate_amount_flow(obj)
                    # obj.save()
                else:  # 退款单状态不可审核
                    Response({"res": "not_in_status"})
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                return Response({"res": "sys_error"})

        if method == "reject":  # 驳回
            try:
                if obj.status in (SaleRefund.REFUND_WAIT_SELLER_AGREE,  # 买家已经申请退款
                                  SaleRefund.REFUND_WAIT_RETURN_GOODS,  # 卖家已经同意退款
                                  SaleRefund.REFUND_CONFIRM_GOODS):  # 买家已经退货
                    obj.status = SaleRefund.REFUND_REFUSE_BUYER  # 修改该退款单为拒绝状态
                    obj.save()
                    log_action(request.user.id, obj, CHANGE, '驳回重申')
                else:  # 退款单状态不可驳回
                    Response({"res": "not_in_status"})
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                return Response({"res": "sys_error"})

        if method == "confirm":  # 确认
            try:
                if obj.status == SaleRefund.REFUND_APPROVE:
                    obj.refund_confirm()
                    obj.save()
                    log_action(request.user.id, obj, CHANGE, '确认退款完成:%s' % obj.refund_id)
                else:
                    Response({"res": "no_complete"})
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                return Response({"res": "sys_error"})

        task_send_msg_for_refund.s(obj).delay()
        return Response({"res": True})

