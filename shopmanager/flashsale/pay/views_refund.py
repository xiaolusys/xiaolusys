# -*- encoding:utf8 -*-
from django.conf import settings
from django.http import Http404, HttpResponseForbidden
from django.views.generic import View
from django.forms import model_to_dict
from django.shortcuts import redirect, get_object_or_404

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.views import APIView

from .models import SaleTrade, SaleOrder, Customer, TradeCharge
from .models_refund import SaleRefund
from . import tasks
import pingpp
import logging

logger = logging.getLogger(__name__)


class RefundApply(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    # permission_classes = (permissions.IsAuthenticated,)
    template_name = "pay/mrefundapply.html"

    def get(self, request, format=None):

        content = request.GET
        user = request.user
        customer = get_object_or_404(Customer, user=request.user)

        trade_id = content.get('trade_id')
        order_id = content.get('order_id')

        sale_order = get_object_or_404(SaleOrder, pk=order_id, sale_trade=trade_id, sale_trade__buyer_id=customer.id)

        if not sale_order.refundable:
            raise Http404

        if sale_order.refund:
            return redirect('refund_confirm', pk=sale_order.refund.id)

        return Response({'order': model_to_dict(sale_order)})

    def post(self, request, format=None):
        content = request.POST
        user = request.user
        trade_id = content.get('trade_id')
        order_id = content.get('order_id')
        return_good = content.get('return_good')
        customer = get_object_or_404(Customer, user=request.user)
        sale_trade = get_object_or_404(SaleTrade, pk=trade_id, buyer_id=customer.id)
        sale_order = get_object_or_404(SaleOrder, pk=order_id, sale_trade=trade_id, sale_trade__buyer_id=customer.id)
        if not sale_order.refundable:
            return HttpResponseForbidden('UNREFUNDABLE')
        if sale_order.refund:
            return redirect('refund_confirm', pk=sale_order.refund.id)

        params = {
            'reason': content.get('reason'),
            'refund_fee': content.get('refund_fee'),
            'desc': content.get('desc'),
            'trade_id': sale_trade.id,
            'order_id': sale_order.id,
            'buyer_id': sale_trade.buyer_id,
            'buyer_nick': sale_trade.buyer_nick,
            'item_id': sale_order.item_id,
            'title': sale_order.title,
            'sku_id': sale_order.sku_id,
            'sku_name': sale_order.sku_name,
            'total_fee': sale_order.total_fee,
            'payment': sale_order.payment,
            'mobile': sale_trade.receiver_mobile,
            'phone': sale_trade.receiver_phone,
            'charge': sale_trade.charge,
        }
        if return_good:
            params.update({'refund_num': content.get('refund_num'),
                           'company_name': content.get('company_name'),
                           'sid': content.get('sid'),
                           'has_good_return': True,
                           'good_status': SaleRefund.BUYER_RECEIVED,
                           'status': SaleRefund.REFUND_WAIT_SELLER_AGREE
                           })

        else:
            good_status = SaleRefund.BUYER_NOT_RECEIVED
            good_receive = content.get('good_receive')
            if good_receive.lower() == 'y':
                good_status = SaleRefund.BUYER_RECEIVED

            params.update({'has_good_return': False,
                           'good_status': good_status,
                           'status': SaleRefund.REFUND_WAIT_SELLER_AGREE
                           })

        sale_refund = SaleRefund.objects.create(**params)

        sale_order.refund_id = sale_refund.id
        sale_order.refund_fee = sale_refund.refund_fee
        sale_order.refund_status = sale_refund.status
        sale_order.save()
        if settings.DEBUG:
            tasks.pushTradeRefundTask(sale_refund.id)
        else:
            tasks.pushTradeRefundTask.delay(sale_refund.id)

        return Response(model_to_dict(sale_refund))


class RefundConfirm(APIView):
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    # permission_classes = (permissions.IsAuthenticated,)
    template_name = "pay/mrefundconfirm.html"

    def get(self, request, pk, format=None):
        customer = get_object_or_404(Customer, user=request.user)
        sale_refund = get_object_or_404(SaleRefund, pk=pk)
        sale_order = get_object_or_404(SaleOrder, pk=sale_refund.order_id,
                                       sale_trade=sale_refund.trade_id,
                                       sale_trade__buyer_id=customer.id)

        refund_dict = model_to_dict(sale_refund)
        refund_dict.update({'created': sale_refund.created,
                            'modified': sale_refund.modified})

        return Response({'order': model_to_dict(sale_order),
                         'refund': refund_dict})

    def post(self, request, pk, format=None):
        return Response({})


from core.options import log_action, User, ADDITION, CHANGE
from flashsale.xiaolumm.models import XiaoluMama, CarryLog
from flashsale.pay.models_user import UserBudget, BudgetLog
from django.db import models
from shopback.trades.models import MergeOrder, MergeTrade
from shopback import paramconfig as pcfg
from tasks import task_send_msg_for_refund


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
        merge_trade = get_object_or_404(MergeTrade, tid=strade.tid)
        refund_dict = model_to_dict(sale_refund)

        refund_dict['refundd_message'] = ""
        if strade.has_budget_paid:  # 如果使用余额
            refund_dict['refundd_message'] = "[1]退回小鹿钱包 {0}元 其中余额{1}".format(strade.payment,
                                                                             strade.payment - strade.pay_cash)
        else:
            refund_dict['refundd_message'] = "[2]退回{0} {1}元".format(strade.get_channel_display(), strade.payment)

        refund_dict['tid'] = strade.tid
        refund_dict['channel'] = strade.get_channel_display()
        refund_dict['pic'] = sale_order.pic_path
        refund_dict['status'] = sale_refund.get_status_display()
        refund_dict['order_status'] = sale_order.get_status_display()
        refund_dict['payment'] = sale_order.payment
        refund_dict['order_s'] = sale_order.status
        refund_dict['pay_time'] = strade.pay_time
        refund_dict['merge_trade_status'] = merge_trade.get_status_display()
        refund_dict['merge_sys_status'] = merge_trade.get_sys_status_display()
        refund_dict['sys_memo'] = merge_trade.sys_memo
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

            tasks.task_update_orderlist.delay(str(obj.sku_id))
            log_action(request.user.id, obj, CHANGE, '保存状态信息到－退货状态')

        if method == "agree":  # 同意退款
            try:
                if obj.status in (SaleRefund.REFUND_WAIT_SELLER_AGREE,
                                  SaleRefund.REFUND_WAIT_RETURN_GOODS,
                                  SaleRefund.REFUND_CONFIRM_GOODS):
                    strade = SaleTrade.objects.get(id=obj.trade_id)
                    sorder = SaleOrder.objects.get(id=obj.order_id)
                    customer = Customer.objects.get(id=strade.buyer_id)
                    if strade.channel == SaleTrade.WALLET:
                        payment = int(obj.refund_fee * 100)
                        xlmm_queryset = XiaoluMama.objects.filter(openid=customer.unionid)
                        xlmm = xlmm_queryset[0]
                        clogs = CarryLog.objects.filter(xlmm=xlmm.id,
                                                        order_num=obj.order_id,  # 以子订单为准
                                                        log_type=CarryLog.REFUND_RETURN)
                        if clogs.exists():
                            total_refund = clogs[0].value + payment  # 总的退款金额　等于已经退的金额　加上　现在要退的金额
                            if total_refund > int(sorder.payment * 100):
                                # 如果钱包总的退款记录数值大于子订单的实际支付额　抛出异常
                                raise Exception(u'超过订单实际支付金额!')
                            else:  # 如果退款总额不大于该笔子订单的实际支付金额　则予以退款操作
                                cl = clogs[0]
                                cl.value = total_refund
                                cl.save()
                                log_action(request.user.id, clogs[0], CHANGE, u'二次退款,退款返现:%s' % clogs[0].id)
                                # 操作记录
                                xlmm_queryset.update(cash=models.F('cash') + payment)
                                obj.status = SaleRefund.REFUND_SUCCESS
                                obj.save()
                                log_action(request.user.id, obj, CHANGE, u'二次退款审核通过:%s' % obj.refund_id)
                        # assert clogs.count() == 0, u'订单已经退款！'
                        else:  # 钱包中不存在该笔子订单的历史退款记录　则创建记录
                            if payment > int(sorder.payment * 100):
                                raise Exception(u'超过订单实际支付金额!')
                            CarryLog.objects.create(xlmm=xlmm.id,
                                                    order_num=obj.order_id,
                                                    buyer_nick=strade.buyer_nick,
                                                    value=payment,
                                                    log_type=CarryLog.REFUND_RETURN,
                                                    carry_type=CarryLog.CARRY_IN,
                                                    status=CarryLog.CONFIRMED)
                            xlmm_queryset.update(cash=models.F('cash') + payment)
                            obj.status = SaleRefund.REFUND_SUCCESS
                            obj.save()
                            log_action(request.user.id, obj, CHANGE, u'首次退款审核通过:%s' % obj.refund_id)
                        obj.refund_Confirm()

                    elif strade.channel == SaleTrade.BUDGET or strade.has_budget_paid:
                        payment = int(obj.refund_fee * 100)
                        blogs = BudgetLog.objects.filter(customer_id=strade.buyer_id,
                                                         referal_id=obj.order_id,  # 以子订单为准
                                                         budget_log_type=BudgetLog.BG_REFUND)
                        if blogs.exists():
                            total_refund = blogs[0].flow_amount + payment  # 总的退款金额　等于已经退的金额　加上　现在要退的金额
                            if total_refund > int(sorder.payment * 100):
                                # 如果钱包总的退款记录数值大于子订单的实际支付额　抛出异常
                                raise Exception(u'超过订单实际支付金额!')
                            else:  # 如果退款总额不大于该笔子订单的实际支付金额　则予以退款操作
                                cl = blogs[0]
                                cl.flow_amount = total_refund
                                cl.save()
                                log_action(request.user.id, blogs[0], CHANGE, u'二次退款,退款返钱包:%s' % blogs[0].id)
                                # 操作记录
                                obj.status = SaleRefund.REFUND_SUCCESS
                                obj.save()
                                log_action(request.user.id, obj, CHANGE, u'二次退款审核通过:%s' % obj.refund_id)

                        else:
                            if payment > int(sorder.payment * 100):
                                raise Exception(u'超过订单实际支付金额!')
                            BudgetLog.objects.create(customer_id=strade.buyer_id,
                                                     referal_id=obj.order_id,
                                                     flow_amount=payment,
                                                     budget_type=BudgetLog.BUDGET_IN,
                                                     budget_log_type=BudgetLog.BG_REFUND,
                                                     status=BudgetLog.CONFIRMED)
                            obj.status = SaleRefund.REFUND_SUCCESS
                            obj.save()
                            log_action(request.user.id, obj, CHANGE, u'首次退款审核通过:%s' % obj.refund_id)
                        obj.refund_Confirm()

                    elif obj.refund_fee > 0 and obj.charge:  # 有支付编号
                        import pingpp

                        pingpp.api_key = settings.PINGPP_APPKEY
                        ch = pingpp.Charge.retrieve(obj.charge)
                        re = ch.refunds.create(description=obj.refund_desc(),
                                               amount=int(obj.refund_fee * 100))
                        obj.refund_id = re.id
                        obj.status = SaleRefund.REFUND_APPROVE  # 确认退款等待返款
                        obj.save()
                        log_action(request.user.id, obj, CHANGE, u'退款审核通过:%s' % obj.refund_id)
                    obj.amount_flow = calculate_amount_flow(obj)
                    obj.save()
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
                    obj.refund_Confirm()
                    obj.save()
                    log_action(request.user.id, obj, CHANGE, '确认退款完成:%s' % obj.refund_id)
                else:
                    Response({"res": "no_complete"})
            except Exception, exc:
                logger.error(exc.message, exc_info=True)
                return Response({"res": "sys_error"})
        task_send_msg_for_refund.s(obj).delay()
        return Response({"res": True})
