# coding=utf-8
"""
退款相关推送
"""
from flashsale.push.mipush import mipush_of_ios, mipush_of_android
from flashsale.protocol import get_target_url
from flashsale.protocol import constants
from flashsale.pay.models import SaleRefund
from models_message import PushMsgTpl


def make_refund_message(refend):
    push_msg_tpls = PushMsgTpl.objects.filter(id__gte=1, id__lte=4, is_valid=True)
    refund_status = refend.status

    if refund_status == SaleRefund.REFUND_WAIT_RETURN_GOODS:  # 同意申请退货
        push_msg_tpls.filter(id=1)

    elif refund_status == SaleRefund.REFUND_REFUSE_BUYER:  # 拒绝申请退款
        push_msg_tpls.filter(id=2)

    elif refund_status == SaleRefund.REFUND_APPROVE:  # 等待返款
        push_msg_tpls.filter(id=3)

    elif refund_status == SaleRefund.REFUND_SUCCESS:  # 退款成功
        push_msg_tpls.filter(id=4)
    else:
        push_msg_tpls = PushMsgTpl.objects.none()

    if push_msg_tpls.exists():
        push_msg_tpl = push_msg_tpls[0]
        return push_msg_tpl.get_emoji_content()
    return None


def push_refund_app_msg(refend):
    """ 发送同意app推送 """
    customer_id = refend.buyer_id
    if customer_id:
        target_url = get_target_url(constants.TARGET_TYPE_REFUNDS)
        message = make_refund_message(refend)
        if message:
            mipush_of_android.push_to_account(customer_id,
                                              {'target_url': target_url},
                                              description=message)
            mipush_of_ios.push_to_account(customer_id,
                                          {'target_url': target_url},
                                          description=message)
