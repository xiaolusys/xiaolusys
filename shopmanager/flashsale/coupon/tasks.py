# coding=utf-8
import logging
import datetime
from celery.task import task
from django.db.models import F, Sum
from flashsale.xiaolumm.models import XiaoluMama

logger = logging.getLogger(__name__)


@task()
def task_update_tpl_released_coupon_nums(template):
    """
    template : CouponTemplate instance
    has_released_count ++ when the CouponTemplate release success.
    """
    from flashsale.coupon.models import UserCoupon

    count = UserCoupon.objects.filter(template_id=template.id).count()
    template.has_released_count = count
    template.save(update_fields=['has_released_count'])
    from django_statsd.clients import statsd
    from django.utils.timezone import now, timedelta

    start = now().date()
    end = start + timedelta(days=1)
    if template.id == 55:
        statsd.timing('coupon.new_customer_released_count',
                      UserCoupon.objects.filter(template_id=template.id, start_use_time__range=(start, end)).count())
    elif template.id == 67:
        statsd.timing('coupon.share_released_count',
                      UserCoupon.objects.filter(template_id=template.id, start_use_time__range=(start, end)).count())
    elif template.id == 86:
        statsd.timing('coupon.old_customer_share_released_count',
                      UserCoupon.objects.filter(template_id=template.id, start_use_time__range=(start, end)).count())
    return


@task()
def task_update_share_coupon_release_count(share_coupon):
    """
    share_coupon : OrderShareCoupon instance
    release_count ++ when the OrderShareCoupon release success
    """
    from flashsale.coupon.models import UserCoupon

    count = UserCoupon.objects.filter(order_coupon_id=share_coupon.id).count()
    share_coupon.release_count = count
    share_coupon.save(update_fields=['release_count'])
    return


@task()
def task_update_coupon_use_count(coupon, trade_tid):
    """
    1. count the CouponTemplate 'has_used_count' field when use coupon
    2. count the OrderShareCoupon 'has_used_count' field when use coupon
    """
    from flashsale.coupon.models import UserCoupon

    coupon.finished_time = datetime.datetime.now()  # save the finished time
    coupon.trade_tid = trade_tid  # save the trade tid with trade be binding
    coupon.save(update_fields=['finished_time', 'trade_tid'])
    tpl = coupon.self_template()

    coupons = UserCoupon.objects.all()
    tpl_used_count = coupons.filter(template_id=tpl.id, status=UserCoupon.USED).count()
    tpl.has_used_count = tpl_used_count
    tpl.save(update_fields=['has_used_count'])

    share = coupon.share_record()
    if share:
        share_used_count = coupons.filter(order_coupon_id=share.id, status=UserCoupon.USED).count()
        share.has_used_count = share_used_count
        share.save(update_fields=['has_used_count'])

    from django_statsd.clients import statsd
    from django.utils.timezone import now, timedelta

    start = now().date()
    end = start + timedelta(days=1)

    if coupon.template_id == 55:
        statsd.timing('coupon.new_customer_used_count', coupons.filter(template_id=tpl.id, status=UserCoupon.USED,
                                                                       finished_time__range=(start, end)).count())
    elif coupon.template_id == 67:
        statsd.timing('coupon.share_used_count', coupons.filter(template_id=tpl.id, status=UserCoupon.USED,
                                                                finished_time__range=(start, end)).count())
    elif coupon.template_id == 86:
        statsd.timing('coupon.old_customer_share_used_count', coupons.filter(template_id=tpl.id, status=UserCoupon.USED,
                                                                             finished_time__range=(start, end)).count())
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
    if not tpl:
        return
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
    from flashsale.coupon.models import CouponTemplate, UserCoupon

    tpl = CouponTemplate.objects.filter(status=CouponTemplate.SENDING,
                                        coupon_type=CouponTemplate.TYPE_MAMA_INVITE).first()
    if not tpl:
        return
    UserCoupon.objects.create_mama_invite_coupon(
        buyer_id=customer.id,
        template_id=tpl.id,
        trade_id=saletrade.id,
        ufrom=ufrom,
    )
    return


@task()
def task_change_coupon_status_used(saletrade):
    coupon_id = saletrade.extras_info.get('coupon') or None
    from flashsale.coupon.models import UserCoupon

    usercoupon = UserCoupon.objects.filter(id=coupon_id,
                                           customer_id=saletrade.buyer_id,
                                           status=UserCoupon.UNUSED
                                           ).first()
    if not usercoupon:
        return
    usercoupon.use_coupon(saletrade.tid)


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


@task()
def task_release_coupon_for_register(instance):
    """
     - release coupon for register a new Customer instance ( when post save created a Customer instance run this task)
    """
    from flashsale.pay.models import Customer

    if not isinstance(instance, Customer):
        return
    from flashsale.coupon.models import UserCoupon

    tpl_ids = [54, 55, 56, 57, 58, 59, 60]
    for tpl_id in tpl_ids:
        try:
            UserCoupon.objects.create_normal_coupon(
                buyer_id=instance.id,
                template_id=tpl_id,
            )
        except:
            logger.error(u'task_release_coupon_for_register for customer id %s' % instance.id)
            continue
    return


@task()
def task_roll_back_usercoupon_by_refund(trade_tid):
    from flashsale.coupon.models import UserCoupon

    cou = UserCoupon.objects.filter(trade_tid=trade_tid).first()
    if cou:
        cou.release_usercoupon()
    return


@task()
def task_update_mobile_download_record(tempcoupon):
    from flashsale.coupon.models import OrderShareCoupon

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


@task()
def task_update_unionid_download_record(usercoupon):
    from flashsale.promotion.models import DownloadUnionidRecord, DownloadMobileRecord

    customer = usercoupon.customer
    if not customer:
        return
    if not customer.unionid.strip():  # 没有unionid  写mobilde 记录
        uni_key = '/'.join([str(usercoupon.share_user_id), str(customer.mobile)])
        dl_record = DownloadMobileRecord.objects.filter(uni_key=uni_key).first()
        if dl_record:  # 记录存在不做处理
            return
        dl_record = DownloadMobileRecord(
            from_customer=usercoupon.share_user_id,
            mobile=customer.mobile,
            ufrom=DownloadMobileRecord.REDENVELOPE,
            uni_key=uni_key)
        dl_record.save()
    else:
        uni_key = '/'.join([str(usercoupon.share_user_id), str(customer.unionid)])
        dl_record = DownloadUnionidRecord.objects.filter(uni_key=uni_key).first()
        if dl_record:  # 记录存在不做处理
            return
        dl_record = DownloadUnionidRecord(
            from_customer=usercoupon.share_user_id,
            ufrom=DownloadMobileRecord.REDENVELOPE,
            unionid=customer.unionid,
            uni_key=uni_key,
            headimgurl=customer.thumbnail,
            nick=customer.nick
        )
        dl_record.save()


@task()
def task_push_msg_pasting_coupon():
    """
    推送：　明天过期的没有推送过的优惠券将推送用户告知
    """
    from flashsale.coupon.models import UserCoupon
    from flashsale.push.push_usercoupon import user_coupon_release_push

    today = datetime.datetime.today()
    tomorow = today + datetime.timedelta(days=1)
    t_left = datetime.datetime(tomorow.year, tomorow.month, tomorow.day, 0, 0, 0)
    t_right = t_left + datetime.timedelta(days=1)
    coupons = UserCoupon.objects.filter(is_pushed=False,
                                        status=UserCoupon.UNUSED,
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


def get_deposit_money(buyer_id):
    from flashsale.xiaolumm.models import CashOut
    from flashsale.pay.models import Customer, SaleTrade

    cusomter = Customer.objects.get(id=buyer_id)
    xlmm = cusomter.get_xiaolumm()
    deposite_cashouts = CashOut.objects.filter(
        xlmm=xlmm.id,
        cash_out_type=CashOut.MAMA_RENEW,
        status__in=[CashOut.COMPLETED, CashOut.APPROVED])
    deposit_trades = SaleTrade.objects.filter(
        buyer_id=buyer_id,
        order_type=SaleTrade.DEPOSITE_ORDER,
        status__in=[SaleTrade.WAIT_SELLER_SEND_GOODS, SaleTrade.TRADE_FINISHED])
    d_m = deposite_cashouts.aggregate(t_v=Sum('value')).get('t_v') or 0
    t_m = deposit_trades.aggregate(t_p=Sum('payment')).get('t_p') or 0
    return d_m / 100.0 + t_m


@task()
def task_release_coupon_for_mama_deposit(buyer_id, deposite_type):
    from flashsale.coupon.models import UserCoupon

    deposite_type_tplids_map = {
        XiaoluMama.HALF: [117, 118,        79],
        XiaoluMama.FULL: [117, 118, 121,   39]
    }
    tpl_ids = deposite_type_tplids_map[deposite_type]

    for template_id in tpl_ids:
        UserCoupon.objects.create_normal_coupon(buyer_id=buyer_id, template_id=template_id)


@task()
def task_release_coupon_for_mama_deposit_double_99(buyer_id):
    """ 续费才进入此方法 """
    from flashsale.coupon.models import UserCoupon

    tpl_ids = [121, 124]  # 100 + 15
    for template_id in tpl_ids:
        UserCoupon.objects.create_normal_coupon(buyer_id=buyer_id, template_id=template_id)

@task()
def task_create_transfer_coupon(sale_order):
    """
    This function temporarily creates UserCoupon. In the future, we should
    create transfer coupon instead.
    """
    from flashsale.coupon.models import UserCoupon
    
    num = sale_order.num
    customer_id = sale_order.sale_trade.buyer_id
    index = 0
    template_id = 153 # transfer_coupon_template
    title = u'小鹿精品专用券'
    coupon_type = UserCoupon.TYPE_TRANSFER
    coupon_value = 128
    trade_tid = sale_order.sale_trade.tid
    start_time = datetime.datetime.now()
    end_time = datetime.datetime(start_time.year+5,start_time.month,start_time.day)

    while index < num:
        uni_key = UserCoupon.create_transfer_coupon_unikey(order_id, index)

        coupon = UserCoupon(template_id=template_id,title=title,coupon_type=coupon_type,customer_id=customer_id,
                            coupon_no=uni_key,value=coupon_value,trade_tid=trade_tid,start_use_time=start_time,
                            expires_time=end_time,uniq_id=uni_key)
        coupon.save()
        
        index += 1
