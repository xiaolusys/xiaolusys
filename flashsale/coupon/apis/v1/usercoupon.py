# coding=utf-8
from __future__ import unicode_literals, absolute_import
from flashsale.pay.apis.v1.customer import get_customer_by_id
from ...tasks.usercoupon import task_release_coupon_for_deposit, task_update_tpl_released_coupon_nums, \
    task_update_share_coupon_release_count
from ...models.usercoupon import UserCoupon
from .coupontemplate import get_coupon_template_by_id
from .ordersharecoupon import get_order_share_coupon_by_id

__ALL__ = [
    'release_coupon_for_mama_deposit'
]


def _check_template(template):
    # type: (CouponTemplate) -> bool
    """优惠券检查
    """
    template.template_valid_check()  # 有效性检查
    template.check_date()  # 时间检查
    return True


def _check_target_user(customer, template):
    # type: (Customer, CouponTemplate) -> bool
    """身份判定（判断身份是否和优惠券模板指定用户一致） 注意　这里是硬编码　和　XiaoluMama　代理级别关联
    """
    user_level = template.TARGET_ALL
    if template.target_user != template.TARGET_ALL:  # 如果不是所有用户可领取则判定级别
        xlmm = customer.getXiaolumm()
        if xlmm:
            user_level = xlmm.agencylevel  # 用户的是代理身份 内1 　VIP 2  A 3
    if user_level != template.target_user:  # 如果用户领取的优惠券和用户身份不一致则不予领取
        return True
    return False


def _check_template_release_num(template):
    # type: (CouponTemplate) -> bool
    """优惠券发放数量检查
    """
    coupons = UserCoupon.objects.filter(template_id=template.id).exclude(status=UserCoupon.CANCEL)
    tpl_release_count = coupons.count()  # 当前模板的优惠券条数
    if tpl_release_count > template.prepare_release_num:  # 如果大于定义的限制领取数量
        return False
    return True


def _check_saletrade(trade_id):
    """ 检查交易 """
    from flashsale.pay.models import SaleTrade

    trade = SaleTrade.objects.filter(id=trade_id).first()
    if trade is None:  # 没有该订单存在
        return None, 8, u'绑定订单不存在'
    return trade, 0, u"订单id正确"


def release_coupon_for_deposit(customer_id, deposit_type):
    # type: (int, int) -> None
    """release coupon for deposit
    """
    task_release_coupon_for_deposit.delay(customer_id, deposit_type)


def create_user_coupon(customer_id, coupon_template_id,
                       trade_id=None, cash_out_id=None, order_share_id=None, coupon_value=None,
                       ufrom='wap', **kwargs):
    # type: (int, int, text_type, **Any) ->Tuple[Optional[UserCoupon], int, text_type]
    """创建普通类型优惠券, 这里不计算领取数量(默认只能领取一张 不填写 uniq_id的张数内容)
    """
    tpl = get_coupon_template_by_id(coupon_template_id)
    customer = get_customer_by_id(customer_id)
    if not _check_target_user(customer, tpl):
        return None, 1, 'not for current user'
    if not _check_template(tpl):
        return None, 2, 'not valid template'
    if not _check_template_release_num(tpl):
        return None, 3, 'coupon is send out'
    value, start_use_time, expires_time = tpl.calculate_value_and_time()
    extras = {'user_info': {'id': customer.id, 'nick': customer.nick, 'thumbnail': customer.thumbnail}}

    unique_key = tpl.make_uniq_id(tpl, customer.id)
    if trade_id:
        unique_key = tpl.make_uniq_id(customer.id, trade_id=trade_id)
    if cash_out_id:
        unique_key = tpl.make_uniq_id(customer.id, cashout_id=cash_out_id)
    if order_share_id:
        share_coupon = get_order_share_coupon_by_id(order_share_id)

    cou = UserCoupon.objects.filter(uniq_id=unique_key).first()
    if cou:
        return cou, 4, u'已经领取'
    cou = UserCoupon.objects.create(template_id=coupon_template_id,
                                    title=tpl.title,
                                    coupon_type=tpl.coupon_type,
                                    customer_id=customer_id,
                                    value=value,
                                    start_use_time=start_use_time,
                                    expires_time=expires_time,
                                    ufrom=ufrom,
                                    uniq_id=unique_key,
                                    extras=extras)
    task_update_tpl_released_coupon_nums.delay(tpl)
    return cou, 0, u"领取成功"


def create_order_share_coupon(self, buyer_id, template_id, order_share_id=None, ufrom=None, coupon_value=None,
                              **kwargs):
    """
    创建订单分享优惠券
    # 如果是分享类型 判断批次领取
    """
    batch_coupon = user_coupons.filter(order_coupon_id=share_coupon.id).first()
    if batch_coupon:  # 如果该批次号已经领取过了 则返回优惠券(订单分享的订单仅能领取一个优惠券)
        return batch_coupon, 0, u'已经领取'
    if not share_coupon.release_count < share_coupon.limit_share_count:  # 该批次的领取 完了
        return None, 8, u'该分享已领完'  # batch_coupon = None

    value, start_use_time, expires_time = tpl.calculate_value_and_time()
    if coupon_value:  # 如果　指定了　优惠券价值（根据临时优惠券生成用户优惠券的时候）
        value = coupon_value
    uniq_id = make_uniq_id(tpl, customer.id, share_id=share_coupon.id)
    extras = {'user_info': {'id': customer.id, 'nick': customer.nick, 'thumbnail': customer.thumbnail}}
    cou = UserCoupon.objects.create(template_id=int(template_id),
                                    title=tpl.title,
                                    coupon_type=tpl.coupon_type,
                                    customer_id=int(buyer_id),
                                    share_user_id=share_coupon.share_customer,
                                    order_coupon_id=share_coupon.id,
                                    value=value,
                                    start_use_time=start_use_time,
                                    expires_time=expires_time,
                                    ufrom=ufrom,
                                    uniq_id=uniq_id,
                                    extras=extras)
    # update the release num
    task_update_tpl_released_coupon_nums.delay(tpl)
    # update the share_coupon.release_count
    task_update_share_coupon_release_count.delay(share_coupon)
    return cou, 0, u"领取成功"


def create_active_share_coupon(self, buyer_id, template_id, share_uniq_id=None, ufrom=None, **kwargs):
    """
    创建活动分享优惠券
    # 如果是分享类型 判断批次领取
    share_uniq_id: 活动id + customer (一个用户 一个活动只能参加一次)
    """
    from flashsale.coupon.models import UserCoupon, CouponTemplate, OrderShareCoupon

    ufrom = ufrom or ''
    share_uniq_id = share_uniq_id or ''
    if not (buyer_id and template_id):
        return None, 7, u'没有发放'
    share_coupon = OrderShareCoupon.objects.filter(uniq_id=share_uniq_id).first()
    if not share_coupon:  # 如果分享类型没有uniq_id号码则不予领取优惠券
        return None, 1, u"没有领取到呢"

    tpl, code, tpl_msg = check_template(template_id)  # 优惠券检查
    if not tpl:  # 没有找到模板或者没有
        return tpl, code, tpl_msg
    if tpl.coupon_type != CouponTemplate.TYPE_ACTIVE_SHARE:  # 模板类型不是 活动分享 类型 则抛出异常
        raise AssertionError(u'领取优惠券类型有误!')
    customer, code, cu_msg = check_target_user(buyer_id, tpl)  # 用户身份检查
    if not customer:
        return customer, code, cu_msg

    coupons, code, tpl_n_msg = check_template_release_nums(tpl, template_id)  # 优惠券存量检查
    if coupons is None:
        return coupons, code, tpl_n_msg

    user_coupons = coupons.filter(customer_id=int(buyer_id))

    batch_coupon = user_coupons.filter(order_coupon_id=share_coupon.id).first()
    if batch_coupon:  # 如果该批次号已经领取过了 则返回优惠券(订单分享的订单仅能领取一个优惠券)
        return batch_coupon, 0, u'已经领取'
    if not share_coupon.release_count < share_coupon.limit_share_count:  # 该批次的领取 完了
        return None, 8, u'该分享已领完'  # batch_coupon = None

    value, start_use_time, expires_time = tpl.calculate_value_and_time()
    uniq_id = make_uniq_id(tpl, customer.id, share_id=share_coupon.id)
    extras = {'user_info': {'id': customer.id, 'nick': customer.nick, 'thumbnail': customer.thumbnail}}
    cou = UserCoupon.objects.create(template_id=int(template_id),
                                    title=tpl.title,
                                    coupon_type=tpl.coupon_type,
                                    customer_id=int(buyer_id),
                                    share_user_id=share_coupon.share_customer,
                                    order_coupon_id=share_coupon.id,
                                    value=value,
                                    start_use_time=start_use_time,
                                    expires_time=expires_time,
                                    ufrom=ufrom,
                                    uniq_id=uniq_id,
                                    extras=extras)
    # update the release num
    task_update_tpl_released_coupon_nums.delay(tpl)
    # update the share_coupon.release_count
    task_update_share_coupon_release_count.delay(share_coupon)
    return cou, 0, u"领取成功"
