# coding=utf-8
from __future__ import unicode_literals, absolute_import
import datetime
from django.db import IntegrityError
from django.db import transaction
from rest_framework import exceptions
from ...models.transfer_coupon import CouponTransferRecord
from ...models.usercoupon import UserCoupon
import logging

logger = logging.getLogger(__name__)

__ALL__ = [
    'create_coupon_transfer_record',
]


def create_present_coupon_transfer_record(customer, template, coupon_id, uni_key_prefix=None):
    # type: (Customer, CouponTemplate, int, Optional[int]) -> CouponTransferRecord
    """创建赠送优惠券流通记录
    """
    to_mama = customer.get_charged_mama()
    to_mama_nick = customer.nick
    to_mama_thumbnail = customer.thumbnail

    coupon_to_mama_id = to_mama.id
    init_from_mama_id = to_mama.id

    coupon_from_mama_id = 0
    from_mama_thumbnail = 'http://7xogkj.com2.z0.glb.qiniucdn.com/222-ohmydeer.png?imageMogr2/thumbnail/60/format/png'
    from_mama_nick = 'SYSTEM'

    transfer_type = CouponTransferRecord.IN_GIFT_COUPON
    date_field = datetime.date.today()
    transfer_status = CouponTransferRecord.DELIVERED
    uni_key_prefix = 'gift-%s' % uni_key_prefix if uni_key_prefix else 'gift'
    uni_key = "%s-%s-%s" % (uni_key_prefix, to_mama.id, coupon_id)
    order_no = 'gift-%s' % coupon_id
    coupon_value = int(template.value)
    product_img = template.extras.get("product_img") or ''

    try:
        coupon = CouponTransferRecord(coupon_from_mama_id=coupon_from_mama_id, from_mama_thumbnail=from_mama_thumbnail,
                                      from_mama_nick=from_mama_nick, coupon_to_mama_id=coupon_to_mama_id,
                                      to_mama_thumbnail=to_mama_thumbnail, to_mama_nick=to_mama_nick,
                                      coupon_value=coupon_value,
                                      init_from_mama_id=init_from_mama_id, order_no=order_no, template_id=template.id,
                                      product_img=product_img, coupon_num=1, transfer_type=transfer_type,
                                      uni_key=uni_key, date_field=date_field, transfer_status=transfer_status)
        coupon.save()
        return coupon
    except Exception as e:
        return e


def send_order_transfer_coupons(customer_id, order_id, order_oid, order_num, product_id):
    # type: (int, int, text_type, int, int) -> None
    from ...tasks import task_send_transfer_coupons

    task_send_transfer_coupons.delay(customer_id, order_id, order_oid, order_num, product_id)


@transaction.atomic
def coupon_exchange_saleorder(customer, order_id, mama_id, exchg_template_id, coupon_num):
    logger.info({
        'message': u'exchange order:customer=%s, mama_id=%s coupon_num=%s order_id=%s templateid=%s' % (
            customer.id, mama_id, coupon_num, order_id, exchg_template_id),
    })

    # (1)sale order置为已经兑换
    from flashsale.pay.models.trade import SaleOrder, SaleTrade
    sale_order = SaleOrder.objects.filter(oid=order_id).first()
    if sale_order:
        if sale_order.status < SaleOrder.WAIT_BUYER_CONFIRM_GOODS:
            logger.warn({
                'message': u'exchange order: order_id=%s status=%s' % (order_id, sale_order.status),
            })
            raise exceptions.ValidationError(u'订单记录状态不对，兑换失败!')
        if sale_order and sale_order.extras.has_key('exchange') and sale_order.extras['exchange'] == True:
            logger.warn({
                'message': u'exchange order: order_id=%s has already exchg' % (order_id),
            })
            raise exceptions.ValidationError(u'订单已经被兑换过了，兑换失败!')
        sale_order.extras['exchange'] = True
        SaleOrder.objects.filter(oid=order_id).update(extras=sale_order.extras)
    else:
        logger.warn({
            'message': u'exchange order: order_id=%s not exist' % (order_id),
        })
        raise exceptions.ValidationError(u'找不到订单记录，兑换失败!')

    # (2)用户优惠券需要变成使用状态
    user_coupons = UserCoupon.objects.filter(customer_id=customer.id, template_id=int(exchg_template_id),
                                             status=UserCoupon.UNUSED)
    use_num = 0
    for coupon in user_coupons:
        if use_num < int(coupon_num):
            UserCoupon.objects.filter(uniq_id=coupon.uniq_id).update(status=UserCoupon.USED, trade_tid=sale_order.oid,
                                                                     finished_time=datetime.datetime.now())
            use_num += 1
        else:
            break

    # (3)在user钱包写收入记录
    from flashsale.pay.models.user import BudgetLog
    today = datetime.date.today()
    order_log = BudgetLog(customer_id=customer.id, flow_amount=round(sale_order.payment * 100),
                          budget_type=BudgetLog.BUDGET_IN,
                          budget_log_type=BudgetLog.BG_EXCHG_ORDER, referal_id=sale_order.id,
                          uni_key=sale_order.oid, status=BudgetLog.CONFIRMED,
                          budget_date=today)

    order_log.save()

    # (4)在精品券流通记录增加兑换记录
    res = CouponTransferRecord.create_exchg_order_record(customer, int(coupon_num), sale_order,
                                                         int(exchg_template_id))

    return res


@transaction.atomic
def saleorder_return_coupon_exchange(salerefund, payment):
    logger.info({
        'message': u'exchange order:customer=%s, payment=%s ' % (
            salerefund.buyer_id, payment),
    })

    #判断这个退款单对应的订单是曾经兑换过的
    from flashsale.pay.models.trade import SaleOrder, SaleTrade
    sale_order = SaleOrder.objects.filter(oid=salerefund.order_id).first()
    if not (sale_order and sale_order.extras.has_key('exchange') and sale_order.extras['exchange'] == True):
        res = {}
        return res

    from flashsale.pay.models.user import UserBudget, Customer
    not_enough_budget = False
    customer = Customer.objects.normal_customer.filter(id=salerefund.buyer_id).first()
    user_budgets = UserBudget.objects.filter(user=customer)
    if user_budgets.exists():
        user_budget = user_budgets[0]
        if user_budget.budget_cash < int(payment):
            not_enough_budget = True

    # (1)在user钱包写支出记录，支出不够变成负数
    from flashsale.pay.models.user import BudgetLog
    today = datetime.date.today()
    order_log = BudgetLog(customer_id=salerefund.buyer_id, flow_amount=int(payment),
                          budget_type=BudgetLog.BUDGET_OUT,
                          budget_log_type=BudgetLog.BG_EXCHG_ORDER, referal_id=salerefund.id,
                          uni_key=salerefund.refund_no, status=BudgetLog.CONFIRMED,
                          budget_date=today)

    order_log.save()

    # (2)sale order置为已经取消兑换
    if sale_order:
        sale_order.extras['exchange'] = False
        SaleOrder.objects.filter(oid=salerefund.order_id).update(extras=sale_order.extras)
    else:
        logger.warn({
            'message': u'return exchange order: order_id=%s not exist' % (salerefund.order_id),
        })
        raise exceptions.ValidationError(u'找不到订单记录，取消兑换失败!')

    # (3)用户优惠券需要变成未使用状态,如果零钱不够扣则变为冻结
    user_coupon = UserCoupon.objects.filter(trade_tid=sale_order.oid,
                                             status=UserCoupon.USED)
    if not not_enough_budget:
        UserCoupon.objects.filter(uniq_id=user_coupon.uniq_id).update(status=UserCoupon.UNUSED, trade_tid='',
                                                                 finished_time='')
    else:
        UserCoupon.objects.filter(uniq_id=user_coupon.uniq_id).update(status=UserCoupon.FREEZE, trade_tid='',
                                                                      finished_time='')

    # (4)在精品券流通记录增加退货退券记录
    res = CouponTransferRecord.gen_return_record(customer, round(payment/sale_order.price),
                                                         int(user_coupon.template_id), sale_order.sale_trade.tid)

    return res