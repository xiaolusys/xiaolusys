# coding=utf-8
from __future__ import unicode_literals, absolute_import
import datetime
from flashsale.pay.apis.v1.customer import get_customer_by_id
from ...models.usercoupon import UserCoupon
from .coupontemplate import get_coupon_template_by_id
from .ordersharecoupon import get_order_share_coupon_by_id
import logging

logger = logging.getLogger(__name__)

__ALL__ = [
    'release_coupon_for_mama_deposit',
    'use_coupon_by_ids',
    'get_user_coupon_by_id',
    'get_user_coupons_by_ids',
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
    coupons = UserCoupon.objects.get_template_coupons(template.id)
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


def get_user_coupon_by_id(id):
    # type: (int) -> UserCoupon
    return UserCoupon.objects.get(id=id)


def get_user_coupons_by_ids(ids):
    # type: (int) -> Optional[List[UserCoupon]]
    return UserCoupon.objects.get_coupons(ids)


def release_coupon_for_deposit(customer_id, deposit_type):
    # type: (int, int) -> None
    """release coupon for deposit
    """
    from ...tasks.usercoupon import task_release_coupon_for_deposit

    task_release_coupon_for_deposit.delay(customer_id, deposit_type)


def create_user_coupon(customer_id, coupon_template_id,
                       unique_key=None, trade_id=None, cash_out_id=None, order_share_id=None, coupon_value=None,
                       ufrom='wap', **kwargs):
    # type: (int, int, text_type, **Any) ->Tuple[Optional[UserCoupon], int, text_type]
    """创建普通类型优惠券, 这里不计算领取数量(默认只能领取一张 不填写 uniq_id的张数内容)
    """
    tpl = get_coupon_template_by_id(coupon_template_id)
    customer = get_customer_by_id(customer_id)
    if not _check_target_user(customer, tpl):
        return None, 1, '未能领取'
    if not _check_template(tpl):
        return None, 2, '无效的优惠券'
    if not _check_template_release_num(tpl):
        return None, 3, u'优惠券已经发完了'
    value, start_use_time, expires_time = tpl.calculate_value_and_time()
    extras = {'user_info': {'id': customer.id, 'nick': customer.nick, 'thumbnail': customer.thumbnail}}
    unique_key = tpl.make_uniq_id(tpl, customer.id) if not unique_key else unique_key
    unique_key = tpl.make_uniq_id(customer.id, trade_id=trade_id) if trade_id else unique_key
    unique_key = tpl.make_uniq_id(customer.id, cashout_id=cash_out_id) if cash_out_id else unique_key

    if order_share_id:
        share_coupon_record = get_order_share_coupon_by_id(order_share_id)
        user_share_coupon = UserCoupon.objects.get_template_coupons(tpl.id).filter(customer_id=customer.id,
                                                                                   order_coupon_id=share_coupon_record.id).first()
        if user_share_coupon:
            return user_share_coupon, 4, u'已经领取分享优惠券'
        if not share_coupon_record.release_count < share_coupon_record.limit_share_count:
            return None, 5, u'该分享券已经领完了'
        unique_key = tpl.make_uniq_id(customer.id, share_id=share_coupon_record.id)
        value = coupon_value if coupon_value else value  # 订单分享的时候（生成临时券value）
        from ...tasks.ordershare_coupon import task_update_share_coupon_release_count

        task_update_share_coupon_release_count.delay(share_coupon_record)  # 更新分享券领取数量
    cou = UserCoupon.objects.filter(uniq_id=unique_key).first()
    if cou:
        return cou, 6, u'已经领取'
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
    from ...tasks.coupontemplate import task_update_tpl_released_coupon_nums

    task_update_tpl_released_coupon_nums.delay(tpl.id)
    return cou, 0, u"领取成功"


def rollback_user_coupon_status_2_unused_by_ids(ids):
    # type: (List[int]) -> None
    UserCoupon.objects.filter(id__in=ids).update(status=UserCoupon.UNUSED)


def use_coupon_by_ids(ids, tid):
    # type: (List[int], text_type) -> bool
    """使用掉优惠券
    """
    from ...tasks.usercoupon import task_update_coupon_use_count

    coupons = get_user_coupons_by_ids(ids)

    for coupon in coupons:
        coupon.coupon_basic_check()  # 检查所有优惠券
    for coupon in coupons:
        coupon.status = UserCoupon.USED
        coupon.finished_time = datetime.datetime.now()  # save the finished time
        coupon.trade_tid = tid  # save the trade tid with trade be binding
        coupon.save(update_fields=['finished_time', 'trade_tid'])
        task_update_coupon_use_count.delay(coupon.template_id, coupon.order_coupon_id)
    return True


def return_user_coupon_by_order_refund(trade_tid, num):
    # type: (text_type, int) -> None
    """交易退款了　退还该交易使用的优惠券
    """
    from ...tasks.usercoupon import task_return_user_coupon_by_trade
    task_return_user_coupon_by_trade.delay(trade_tid, num)

