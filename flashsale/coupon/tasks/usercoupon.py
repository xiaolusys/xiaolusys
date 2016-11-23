# coding=utf-8
from __future__ import absolute_import, unicode_literals
import datetime
from shopmanager import celery_app as app

import logging

logger = logging.getLogger(__name__)


@app.task()
def task_update_coupon_use_count(coupon_template_id, share_coupon_record_id):
    # type: (int, int) -> None
    """更新模板和分享记录　的使用数量字段
    """
    from ..models import UserCoupon
    from ..apis.v1.coupontemplate import get_coupon_template_by_id
    from ..apis.v1.ordersharecoupon import get_order_share_coupon_by_id

    tpl = get_coupon_template_by_id(coupon_template_id)
    tpl_used_count = UserCoupon.objects.get_template_coupons(coupon_template_id).filter(status=UserCoupon.USED).count()
    tpl.has_used_count = tpl_used_count
    tpl.save(update_fields=['has_used_count'])

    if not share_coupon_record_id:  # 不是分享类型优惠券则不统计
        return
    share = get_order_share_coupon_by_id(share_coupon_record_id)
    if share:
        share_used_count = UserCoupon.objects.get_order_share_coupons(share.id).filter(status=UserCoupon.USED).count()
        share.has_used_count = share_used_count
        share.save(update_fields=['has_used_count'])


@app.task()
def task_release_coupon_for_order(saletrade):
    """用户下单给用户发送优惠券(暂时未使用)
    """
    from flashsale.coupon.models import CouponTemplate
    from ..apis.v1.usercoupon import create_user_coupon

    extras_info = saletrade.extras_info
    ufrom = extras_info.get('ufrom')
    tpl = CouponTemplate.objects.filter(status=CouponTemplate.SENDING,
                                        coupon_type=CouponTemplate.TYPE_ORDER_BENEFIT).first()
    if not tpl:
        return
    create_user_coupon(customer_id=saletrade.buyer_id, coupon_template_id=tpl.id, trade_id=saletrade.id,
                       ufrom=str(ufrom))


@app.task()
def task_freeze_coupon_by_refund(salerefund):
    """冻结　因退款（订单购买发放的）优惠券　（暂时未使用）
    """
    from flashsale.coupon.models import UserCoupon

    trade_tid = salerefund.get_tid()
    cous = UserCoupon.objects.filter(trade_tid=trade_tid,
                                     status=UserCoupon.UNUSED)
    if cous.exists():
        cous.update(status=UserCoupon.FREEZE)


@app.task()
def task_release_mama_link_coupon(saletrade):
    """代理链接购买给代理发送优惠券(暂时未使用)
    """
    from flashsale.xiaolumm.models import XiaoluMama
    from flashsale.coupon.models import CouponTemplate
    from ..apis.v1.usercoupon import create_user_coupon

    extras_info = saletrade.extras_info
    mama_id = extras_info.get('mm_linkid') or None
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
    tpl = CouponTemplate.objects.filter(status=CouponTemplate.SENDING,
                                        coupon_type=CouponTemplate.TYPE_MAMA_INVITE).first()
    if not tpl:
        return
    create_user_coupon(customer_id=customer.id, coupon_template_id=tpl.id, trade_id=saletrade.id, ufrom=str(ufrom))


@app.task()
def task_update_user_coupon_status_2_past():
    # type: () -> None
    """更新过期的优惠券状态到过期状态
    """
    from flashsale.coupon.models import UserCoupon

    today = datetime.datetime.today()
    cous = UserCoupon.objects.filter(
        expires_time__lte=today,
        status__in=[UserCoupon.UNUSED, UserCoupon.FREEZE]
    )
    cous.update(status=UserCoupon.PAST)  # 更新为过期优惠券


@app.task()
def task_return_user_coupon_by_trade(trade_tid, num):
    from flashsale.pay.models import Customer
    from ..models.usercoupon import UserCoupon
    from ..models.transfer_coupon import CouponTransferRecord
    from ..apis.v1.usercoupon import rollback_user_coupon_status_2_unused_by_ids

    transfer_coupon_num = 0
    template_id = 0
    customer_id = 0
    for i in range(num):
        cou = UserCoupon.objects.filter(trade_tid=trade_tid, status=UserCoupon.USED).first()
        if cou:
            rollback_user_coupon_status_2_unused_by_ids([cou.id])
        if cou and cou.is_transfer_coupon():
            transfer_coupon_num += 1
            template_id = cou.template_id
            customer_id = cou.customer_id

    if transfer_coupon_num > 0:
        customer = Customer.objects.filter(id=customer_id).first()
        CouponTransferRecord.gen_return_record(customer, transfer_coupon_num, template_id, trade_tid)

    return


@app.task()
def task_update_mobile_download_record(tempcoupon_id):
    # type: (int) -> None
    """更新手机下载记录表(准备弃用)
    """
    from ..models.ordershare_coupon import OrderShareCoupon
    from ..models.tmpshare_coupon import TmpShareCoupon

    tempcoupon = TmpShareCoupon.objects.filter(id=tempcoupon_id).first()
    if not tempcoupon: return
    share = OrderShareCoupon.objects.filter(uniq_id=tempcoupon.share_coupon_id).first()
    if not share:
        return
    from flashsale.promotion.models import DownloadMobileRecord

    uni_key = '/'.join([str(share.share_customer), str(tempcoupon.mobile)])
    dl_record = DownloadMobileRecord.objects.filter(uni_key=uni_key).first()
    if dl_record:  # 记录存在不做处理
        return
    dl_record = DownloadMobileRecord(
        from_customer=share.share_customer,
        mobile=tempcoupon.mobile,
        ufrom=DownloadMobileRecord.REDENVELOPE,
        uni_key=uni_key)
    dl_record.save()


@app.task()
def task_push_msg_pasting_coupon():
    # type: () -> None
    """明天过期的没有推送过的优惠券将推送用户告知
    """
    from flashsale.coupon.models import UserCoupon
    from flashsale.push.push_usercoupon import user_coupon_release_push

    today = datetime.datetime.today()
    tomorow = today + datetime.timedelta(days=1)
    t_left = datetime.datetime(tomorow.year, tomorow.month, tomorow.day, 0, 0, 0)
    t_right = t_left + datetime.timedelta(days=1)
    coupons = UserCoupon.objects.get_unused_coupons().filter(is_pushed=False,
                                                             expires_time__gte=t_left,
                                                             expires_time__lt=t_right)
    customers = coupons.values('customer_id')
    for customer in customers:
        user_coupons = coupons.filter(is_pushed=False, customer_id=customer['customer_id'])
        if user_coupons.exists():
            coupon = user_coupons.first()
            extra_content = '价值%s' % coupon.value
            user_coupon_release_push(coupon.customer_id, push_tpl_id=10, extra_content=extra_content)
        user_coupons.update(is_pushed=True)


@app.task()
def task_release_coupon_for_deposit(customer_id, deposit_type, trade_id=None, cash_out_id=None):
    # type:(int, int, int) -> None
    """发送押金优惠券
    """
    from ..apis.v1.usercoupon import create_user_coupon

    # deposit_type_tplids_map = {
    #     99: [117, 118, 79],  # [121, 124]99+99
    #     188: [117, 118, 121, 39]
    # }
    deposit_type_tplids_map = {
        99: [117, 118, 79],  # [121, 124]99+99
        188: [117, 118, 167, 168, 39]
    }
    if deposit_type not in deposit_type_tplids_map:
        return
    tpl_ids = deposit_type_tplids_map[deposit_type]
    for template_id in tpl_ids:
        create_user_coupon(customer_id=customer_id, coupon_template_id=template_id,
                           trade_id=trade_id, cash_out_id=cash_out_id)
