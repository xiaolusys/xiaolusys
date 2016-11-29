# coding=utf-8
__ALL__ = [
    'get_sale_refund_by_id',
    'create_refund_order',
    'return_fee_by_refund_product',
    'refund_postage',
]
from django.db import transaction
from core.options import log_action, ADDITION, CHANGE
from ...models import SaleOrder, SaleRefund
from ... import tasks

import logging

logger = logging.getLogger(__name__)


def get_sale_refund_by_id(id):
    # type: (int) -> SaleRefund
    return SaleRefund.objects.get(id=id)


def create_refund_order(user_id, order_id, reason, num, refund_fee, refund_channel,
                        desc=None, good_status=None, modify=None, proof_pic=None, **kwargs):
    saleorder = SaleOrder.objects.get(id=order_id)
    refund = saleorder.refund
    if not refund:
        refund = saleorder.do_refund(reason=reason,
                                     refund_num=num,
                                     refund_fee=refund_fee,
                                     good_status=good_status,
                                     desc=desc,
                                     refund_channel=refund_channel,
                                     proof_pic=proof_pic)
        log_action(user_id, refund, ADDITION, u'创建退款单')
    else:
        return refund

    update_fields = []
    for name, value in kwargs.iteritems():
        if hasattr(refund, name):
            setattr(refund, name, value)
            update_fields.append(name)

    if update_fields:
        refund.save(update_fields=update_fields)

    order_params = {
        "refund_id": refund.id,
        "refund_fee": refund_fee,
        "refund_status": SaleRefund.REFUND_WAIT_SELLER_AGREE
    }
    order_update_fields = []
    # 如果state 为真　则是第一次创建 保存退款退款单信息到SaleOrder中
    for k, v in order_params.iteritems():
        if hasattr(saleorder, k) and getattr(saleorder, k) != v:
            setattr(saleorder, k, v)
            order_update_fields.append(k)
    if order_update_fields:
        saleorder.save(update_fields=order_update_fields)
        log_action(user_id, saleorder, CHANGE, u'退款申请')

    tasks.pushTradeRefundTask.delay(refund.id)
    return refund


def refund_postage(sale_refund, postage_num=0, im_execute=True):
    # type: (SaleRefund, int, bool) -> bool
    """为退款单退邮费
    """
    from flashsale.pay.models import BudgetLog

    if postage_num and postage_num != sale_refund.postage_num:
        sale_refund.postage_num = postage_num
        sale_refund.save(update_fields=['postage_num'])
    if not im_execute:  # 不是立即执行退邮费到用户账户
        return im_execute

    if 0 < sale_refund.postage_num <= 2000:
        BudgetLog.create_salerefund_postage_log(sale_refund, sale_refund.postage_num)
        return True
    return False


def refund_coupon(sale_refund, amount_flow=None, im_execute=True):
    # type : (SaleRefund, Optional[Dict[str, *Ant]], bool) -> bool
    """补邮费优惠券给用户
    """
    from flashsale.coupon.apis.v1.usercoupon import create_user_coupon

    if amount_flow and amount_flow != sale_refund.amount_flow:
        sale_refund.amount_flow = amount_flow
        sale_refund.save(update_fields=['amount_flow'])
    if not im_execute:
        return im_execute
    try:
        if isinstance(sale_refund.amount_flow, dict):
            refund_coupon_info = sale_refund.amount_flow.get('refund_coupon')
            if refund_coupon_info:
                coupon_template_id = refund_coupon_info.get('template_id')
                send_status = refund_coupon_info.get('send_status')
                if coupon_template_id and not send_status:
                    cou, code, msg = create_user_coupon(sale_refund.buyer_id, coupon_template_id,
                                                        trade_id=sale_refund.trade_id)
                    if code == 0:
                        refund_coupon_info.update({
                            'send_status': True,
                            'coupon_id': cou.id,
                            'coupon_value': cou.value}
                        )
                        sale_refund.amount_flow.update({
                            'refund_coupon': refund_coupon_info
                        })
                        sale_refund.save(update_fields=['amount_flow'])
                        return True
    except Exception as e:
        logger.error({'action': u'refund_coupon %s' % sale_refund.id, 'message': e.message})
        return False
    return False


@transaction.atomic()
def return_fee_by_refund_product(sale_refund):
    # type: (SaleRefund) -> bool
    """根据　refund app 的RefundProduct 来给用户退款
    """
    if sale_refund.good_status != SaleRefund.BUYER_RETURNED_GOODS \
            or sale_refund.status != SaleRefund.REFUND_CONFIRM_GOODS:
        logger.error({'action': u'return_fee_by_refund_product',
                      'message': u'退款单状态错误 不予退款',
                      'salerefund': sale_refund.id})
        return False
    refund_postage(sale_refund)  # 补邮费
    refund_coupon(sale_refund)  # 补优惠券
    sale_refund.refund_fast_approve()  # 退订单金额(退款成功)　
    return True
