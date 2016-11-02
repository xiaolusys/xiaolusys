# coding:utf-8
from celery import task

from core.options import log_action, ADDITION, CHANGE
from flashsale.pay.models import SaleOrder, SaleRefund
from flashsale.pay import tasks


@task()
def api_create_refund_order(user_id, order_id, reason, num, refund_fee, refund_channel,
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

