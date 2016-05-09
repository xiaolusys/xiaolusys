# coding=utf-8
import datetime
from celery.task import task
from django.db.models import F
from flashsale.xiaolumm.models import XiaoluMama


@task()
def task_update_tpl_released_coupon_nums(template):
    """
    template : CouponTemplate instance
    has_released_count ++ when the CouponTemplate release success.
    """
    template.has_released_count = F('has_released_count') + 1
    template.save(update_fields=['has_released_count'])
    return


@task()
def task_update_share_coupon_release_count(share_coupon):
    """
    share_coupon : OrderShareCoupon instance
    release_count ++ when the OrderShareCoupon release success
    """
    share_coupon.release_count = F('release_count') + 1
    share_coupon.save(update_fields=['release_count'])
    return


@task()
def task_update_coupon_use_count(coupon, trade_tid):
    """
    1. count the CouponTemplate 'has_used_count' field when use coupon
    2. count the OrderShareCoupon 'has_used_count' field when use coupon
    """
    coupon.finished_time = datetime.datetime.now()  # save the finished time
    coupon.trade_tid = trade_tid  # save the trade tid with trade be binding
    coupon.save(update_fields=['finished_time'])
    tpl = coupon.self_template()
    tpl.has_used_count = F('has_used_count') + 1
    tpl.save(update_fields=['has_used_count'])

    share = coupon.share_record()
    if share:
        share.has_used_count = F('has_used_count') + 1
        share.save(update_fields=['has_used_count'])
    return


@task()
def task_release_coupon_for_order(saletrade):
    """
    - SaleTrade pay confirm single to drive this task.
    """
    from flashsale.coupon.models import CouponTemplate, UserCoupon

    extras_info = saletrade.extras_info
    ufrom = extras_info.get('ufrom')
    tpl = CouponTemplate.objects.filter(status=CouponTemplate.SENDING,
                                        coupon_type=CouponTemplate.TYPE_ORDER_BENEFIT).first()
    UserCoupon.objects.create_mama_invite_coupon(
        buyer_id=saletrade.buyer_id,
        template_id=tpl.id,
        trade_id=saletrade.id,
        ufrom=ufrom,
    )
    return


@task()
def task_freeze_coupon_by_refund(salerefund):
    """
    - SaleRefund refund signal to drive this task.
    """
    from flashsale.coupon.models import UserCoupon

    trade_tid = salerefund.get_tid()
    cous = UserCoupon.objects.filter(trade_tid=trade_tid,
                                     status=UserCoupon.UNUSED)
    if cous.exists():
        cous.update(status=UserCoupon.FREEZE)


@task()
def task_release_mama_link_coupon(saletrade):
    """
    - SaleTrade pay confirm single to drive this task
    - when a customer buy a trade with the mama link url then release a coupon for that mama.
    """
    extras_info = saletrade.extras_info
    mama_id = extras_info.get('mm_linkid')
    ufrom = extras_info.get('ufrom')

    order = saletrade.sale_orders.all().first()
    if order and order.item_id in ['22030', '14362', '2731']:  # spacial product id
        return

    if not mama_id:
        return
    mama = XiaoluMama.objects.filter(id=mama_id, charge_status=XiaoluMama.CHARGED).first()
    if not mama:
        return
    customer = mama.get_mama_customer()
    if not customer:
        return
    from flashsale.coupon.models import CouponTemplate, UserCoupon

    tpl = CouponTemplate.objects.filter(status=CouponTemplate.SENDING,
                                        coupon_type=CouponTemplate.TYPE_MAMA_INVITE).first()
    UserCoupon.objects.create_mama_invite_coupon(
        buyer_id=customer.id,
        template_id=tpl.id,
        trade_id=saletrade.id,
        ufrom=ufrom,
    )
    return


@task()
def task_change_coupon_status_used(saletrade):
    coupon_id = saletrade.extras_info.get('coupon')
    from flashsale.coupon.models import UserCoupon

    usercoupon = UserCoupon.objects.filter(id=coupon_id, customer_id=saletrade.buyer_id).first()
    if not usercoupon:
        return
    usercoupon.use_coupon()


@task()
def task_update_user_coupon_status_2_past():
    """
    - timing to update the user coupon to past.
    """
    from flashsale.coupon.models import UserCoupon

    today = datetime.datetime.today()
    cous = UserCoupon.objects.filter(
        expires_time__lte=today,
        status__in=[UserCoupon.UNUSED, UserCoupon.FREEZE]
    )
    cous.update(status=UserCoupon.PAST)  # 更新为过期优惠券
