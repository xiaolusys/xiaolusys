# coding=utf-8
from flashsale.pay.models_refund import SaleRefund
from flashsale.pay.models import SaleOrder
from shopback.refunds.models import REFUND_REASON
from shopback.base import log_action, ADDITION, CHANGE
from django.shortcuts import get_object_or_404
from rest_framework import exceptions
from common.modelutils import update_model_fields
from flashsale.pay.tasks import pushTradeRefundTask
from flashsale.pay.signals import signal_saletrade_refund_post
import math


def save_Other_Atriibut(order=None, sale_refund=None, refund_num=None, reason=None, desc=None,
                        good_status=None):
    sale_refund.buyer_id = order.sale_trade.buyer_id
    sale_refund.title = order.title
    sale_refund.charge = order.sale_trade.charge
    sale_refund.item_id = int(order.item_id) if order.item_id else 0
    sale_refund.sku_id = int(order.sku_id) if order.sku_id else 0
    sale_refund.sku_name = order.sku_name
    sale_refund.refund_num = refund_num
    sale_refund.buyer_nick = order.sale_trade.buyer_nick
    sale_refund.mobile = order.sale_trade.receiver_mobile
    sale_refund.phone = order.sale_trade.receiver_phone
    sale_refund.total_fee = order.total_fee
    sale_refund.payment = order.payment
    sale_refund.refund_fee = order.refund_fee
    sale_refund.reason = REFUND_REASON[reason][1]  # 填写原因
    sale_refund.desc = desc
    sale_refund.good_status = good_status  # 退货状态
    update_model_fields(sale_refund,
                        update_fields=['buyer_id', 'title', 'charge', 'item_id', 'sku_id', 'sku_name', 'refund_num',
                                       'buyer_nick', 'mobile', 'phone', 'total_fee', 'payment', 'refund_fee', 'reason',
                                       'desc', 'good_status'])


def common_Handler(customer=None, order=None, reason=None, num=None, refund_fee=None, desc=None, refund_type=None,
                   modify=None):
    if num == 0 or None:  # 提交的退款产品数量为0
        raise exceptions.APIException(u'退货数量为0')
    if num > order.num:
        raise exceptions.APIException(u'退货数量超过购买数量')
    # 退款处理　生成退款单
    if refund_fee > (order.payment / order.num) * num:  # 退款金额不能大于 单价乘以退款数量
        raise exceptions.APIException(u'退货金额大于实付款')
    sale_refund, state = SaleRefund.objects.get_or_create(trade_id=order.sale_trade.id, order_id=order.id)
    if state:
        # 如果state 为真　则是第一次创建
        order.refund_id = sale_refund.id  # refund_id
        order.refund_fee = refund_fee  # 退款费用为申请的费用
        order.refund_status = SaleRefund.REFUND_WAIT_SELLER_AGREE  # 已经申请退款状态
        update_model_fields(order, update_fields=['refund_id', 'refund_fee', 'refund_status'])
        log_action(customer, order, CHANGE, u'用户售后提交申请时修改order信息！')
        # 保存其他信息到 sale_refund
        save_Other_Atriibut(order=order, sale_refund=sale_refund, refund_num=num, good_status=refund_type,
                            reason=reason, desc=desc)
        log_action(customer, sale_refund, ADDITION, u'用户售后增加退货款单信息！')
        # 发送信号退款
        signal_saletrade_refund_post.send(sender=SaleRefund, obj=sale_refund)
        pushTradeRefundTask(sale_refund.id)
    elif modify == 1 and state is False:  # 有退款单
        # 修改该订单的
        if sale_refund.status in (
                SaleRefund.REFUND_SUCCESS, SaleRefund.REFUND_WAIT_RETURN_GOODS, SaleRefund.REFUND_APPROVE,
                SaleRefund.REFUND_CLOSED):  # 退款成功 等待返款 同意退款 退款关闭  之后不允许修改
            raise exceptions.APIException(u'退款已被受理或关闭,不予用户自行修改')
        order.refund_fee = refund_fee
        order.refund_status = SaleRefund.REFUND_WAIT_SELLER_AGREE  # 修改该到提交申请状态
        update_model_fields(order, update_fields=['refund_id', 'refund_fee', 'refund_status'])
        log_action(customer, order, CHANGE, u'用户售后被拒绝后修改order信息！')
        sale_refund.status = SaleRefund.REFUND_WAIT_SELLER_AGREE
        update_model_fields(sale_refund, update_fields=['status'])
        # 保存其他信息到sale_refund
        save_Other_Atriibut(order=order, sale_refund=sale_refund, refund_num=num, good_status=refund_type,
                            reason=reason, desc=desc)
        pushTradeRefundTask(sale_refund.id)


def modify_refund(customer, company, oid, sid):
    order = get_object_or_404(SaleOrder, id=oid)
    refund = get_object_or_404(SaleRefund, order_id=oid)
    if refund.status in (SaleRefund.REFUND_SUCCESS, SaleRefund.REFUND_APPROVE, SaleRefund.REFUND_CLOSED):
        # 退款成功 等待返款 退款关闭  之后不允许修改 物流信息
        raise exceptions.APIException(u'退款已被受理或关闭,不予用户自行修改物流信息')
    order.refund_status = SaleRefund.REFUND_CONFIRM_GOODS
    update_model_fields(order, update_fields=['refund_status'])
    log_action(customer, order, CHANGE, u'用户退货填写物流信息,修改order　refund_status 到买家退货状态！')

    refund.company_name = company
    refund.sid = sid
    refund.status = SaleRefund.REFUND_CONFIRM_GOODS  # 修改到买家已经退货状态
    refund.good_status = SaleRefund.BUYER_RETURNED_GOODS  # 修改商品状态到买家已经退货

    update_model_fields(refund, update_fields=['company_name', 'sid', 'status', 'good_status'])
    log_action(customer, refund, CHANGE, u'用户退货填写物流信息！')


def apply_fee_handler(num=None, order=None):
    """ 计算退款费用　"""
    if num == 0 or None:  # 提交的退款产品数量为0
        raise exceptions.APIException(u'退货数量为0')
    if num == order.num:  # 退款数量等于购买数量 全额退款
        apply_fee = order.payment  # 申请费用
    else:
        apply_fe = ((order.payment / order.num) * num)  # 申请费用
        apply_fee = math.floor(apply_fe * 100) / 100
    return apply_fee


def refund_Handler(request):
    content = request.REQUEST
    modify = int(content.get("modify", 0))
    company = content.get("company", '')
    sid = content.get("sid", '')
    oid = int(content.get("id", 0))
    customer = request.user.id
    reason = int(request.data.get("reason", "0"))
    num = int(request.data.get("num", 0))
    desc = request.data.get("description", '')

    if modify == 2:  # 修改该物流信息
        modify_refund(customer, company, oid, sid)
    elif modify == 3:  # 修改数量返回退款金额
        order, refund_type = refund_Status(order_id=oid)
        apply_fee = apply_fee_handler(num=num, order=order)
        return {"apply_fee": apply_fee}
    else:
        # 验证处理订单的状态即退款状态
        order, refund_type = refund_Status(order_id=oid)
        refund_fee = apply_fee_handler(num=num, order=order)  # 计算退款费用
        leavings = order.payment - order.refund_fee
        if refund_fee > leavings:
            raise exceptions.APIException(u'退款金额异常请联系客服处理')
        common_Handler(customer=customer, reason=reason, num=num, refund_fee=refund_fee, desc=desc,
                       refund_type=refund_type, order=order, modify=modify)
    return {"res": "ok"}


def refund_Status(order_id=None):
    order = get_object_or_404(SaleOrder, id=order_id)
    # 如果Order已经付款 refund_type = BUYER_NOT_RECEIVED
    # 如果Order 仅仅签收状态才可以退货  refund_type = BUYER_RECEIVED
    if order.status == SaleOrder.WAIT_SELLER_SEND_GOODS:
        refund_type = SaleRefund.BUYER_NOT_RECEIVED
    elif order.status in (SaleOrder.TRADE_BUYER_SIGNED,):
        refund_type = SaleRefund.BUYER_RECEIVED
    else:
        raise exceptions.APIException(u'订单状态不予退款或退货')
    return order, refund_type