# coding=utf-8
from __future__ import unicode_literals, absolute_import
import datetime
from django.db import transaction

from flashsale.pay.apis.v1.customer import get_customer_by_id, get_customer_by_unionid
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
    'get_freeze_boutique_coupons_by_transfer',
    'get_will_return_coupons_by_transfer_id',
    'transfer_coupon',
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
        return False
    return True


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


def get_freeze_boutique_coupons_by_transfer(transfer_record_id, customer_id=None):
    # type: (int, Optional[int]) -> Optional[List[UserCoupon]]
    """通过流通券记录　获取冻结状态的精品券
    """
    freeze_boutiques = UserCoupon.objects.get_freeze_boutique_coupons()
    if customer_id:
        freeze_boutiques = freeze_boutiques.filter(customer_id=customer_id)
    coupons = freeze_boutiques.filter(extras__contains='"freeze_by_transfer_id": "%s"' % transfer_record_id)
    return coupons


def release_coupon_for_deposit(customer_id, deposit_type, trade_id=None, cash_out_id=None):
    # type: (int, int, int) -> None
    """release coupon for deposit
    """
    from ...tasks import task_release_coupon_for_deposit

    task_release_coupon_for_deposit.delay(customer_id, deposit_type, trade_id=trade_id, cash_out_id=cash_out_id)


def create_user_coupon(customer_id, coupon_template_id,
                       unique_key=None, trade_id=None, cash_out_id=None, order_share_id=None, coupon_value=None,
                       ufrom='wap', **kwargs):
    # type: (int, int, Optional[text_type], Optional[int], Optional[int],
    # Optional[int], Optional[float], Optional[text_type], **Any) ->Tuple[Optional[UserCoupon], int, text_type]
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
    unique_key = tpl.make_uniq_id(customer.id) if not unique_key else unique_key
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
    cou = UserCoupon.objects.filter(uniq_id=unique_key).first()
    if cou:
        return cou, 6, u'已经领取'
    cou = UserCoupon(template_id=coupon_template_id,
                     title=tpl.title,
                     coupon_type=tpl.coupon_type,
                     customer_id=customer_id,
                     value=value,
                     start_use_time=start_use_time,
                     expires_time=expires_time,
                     ufrom=ufrom,
                     uniq_id=unique_key,
                     extras=extras)
    cou.save()
    if order_share_id:
        from ...tasks import task_update_share_coupon_release_count

        cou.order_coupon_id = share_coupon_record.id
        cou.save(update_fields=['order_coupon_id'])
        task_update_share_coupon_release_count.delay(share_coupon_record.id)  # 更新分享券领取数量
    from ...tasks import task_update_tpl_released_coupon_nums

    task_update_tpl_released_coupon_nums.delay(tpl.id)
    return cou, 0, u"领取成功"


def create_boutique_user_coupon(customer, tpl, unique_key=None, ufrom='wap', **kwargs):
    # type: (Customer, CouponTemplate, Optional[text_type], text_type, **Any) ->
    # Tuple[Optional[UserCoupon], int, text_type]
    """创建boutique类型优惠券
    """
    if not _check_target_user(customer, tpl):
        return None, 1, '未能领取'
    if not _check_template(tpl):
        return None, 2, '无效的优惠券'
    if not _check_template_release_num(tpl):
        return None, 3, u'优惠券已经发完了'
    value, start_use_time, expires_time = tpl.calculate_value_and_time()
    extras = {'user_info': {'id': customer.id, 'nick': customer.nick, 'thumbnail': customer.thumbnail}}
    unique_key = tpl.make_uniq_id(customer.id) if not unique_key else unique_key

    cou = UserCoupon.objects.filter(uniq_id=unique_key).first()
    if cou:
        return cou, 6, u'已经领取'
    cou = UserCoupon(template_id=tpl.id,
                     title=tpl.title,
                     coupon_type=tpl.coupon_type,
                     customer_id=customer.id,
                     value=value,
                     start_use_time=start_use_time,
                     expires_time=expires_time,
                     ufrom=ufrom,
                     uniq_id=unique_key,
                     extras=extras)
    cou.save()
    return cou, 0, u"领取成功"


def rollback_user_coupon_status_2_unused_by_ids(ids):
    # type: (List[int]) -> None
    UserCoupon.objects.filter(id__in=ids).update(status=UserCoupon.UNUSED)


def use_coupon_by_ids(ids, tid):
    # type: (List[int], text_type) -> bool
    """使用掉优惠券
    """
    from ...tasks import task_update_coupon_use_count

    coupons = get_user_coupons_by_ids(ids)

    for coupon in coupons:
        coupon.coupon_basic_check()  # 检查所有优惠券
    for coupon in coupons:
        coupon.status = UserCoupon.USED
        coupon.finished_time = datetime.datetime.now()  # save the finished time
        coupon.trade_tid = tid  # save the trade tid with trade be binding
        coupon.save(update_fields=['finished_time', 'trade_tid', 'status'])
        task_update_coupon_use_count.delay(coupon.template_id, coupon.order_coupon_id)
    return True


def return_user_coupon_by_order_refund(trade_tid, num):
    # type: (text_type, int) -> None
    """交易退款了　退还该交易使用的优惠券
    """
    from ...tasks import task_return_user_coupon_by_trade

    task_return_user_coupon_by_trade.delay(trade_tid, num)


def freeze_transfer_coupon(coupon_ids, transfer_id):
    # type : (List[int], int) -> bool
    """ 冻结申请的　退还上级的　优惠券
    """
    coupons = get_user_coupons_by_ids(coupon_ids)
    for coupon in coupons:
        coupon.status = UserCoupon.FREEZE
        coupon.extras['freeze_by_transfer_id'] = str(transfer_id)
        coupon.save(update_fields=['status', 'customer_id', 'extras', 'modified'])
    return True


def cancel_coupon_by_ids(coupon_ids):
    # type: (List[int]) -> bool
    """取消 优惠券
    """
    coupons = get_user_coupons_by_ids(coupon_ids)
    for coupon in coupons:
        coupon.status = UserCoupon.CANCEL
        coupon.save(update_fields=['status', 'modified'])
    return True


@transaction.atomic()
def return_transfer_coupon(coupons):
    # type : (List[UserCoupon], int) -> bool
    """ 给 流通券退回上级　妈妈
    """
    from .transfer import get_transfer_record_by_id, set_transfer_record_complete
    from flashsale.xiaolumm.apis.v1.xiaolumama import get_mama_by_id
    from flashsale.xiaolumm.tasks.tasks_mama_dailystats import task_calc_xlmm_elite_score

    mama_ids = set()
    for coupon in coupons:
        will_return_2_transfer_id = coupon.extras.get('freeze_by_transfer_id')
        if not will_return_2_transfer_id:
            continue
        will_return_2_transfer_id = int(will_return_2_transfer_id)
        transfer = get_transfer_record_by_id(will_return_2_transfer_id)
        set_transfer_record_complete(transfer)
        to_mama = get_mama_by_id(transfer.coupon_to_mama_id)
        customer = get_customer_by_unionid(to_mama.openid)
        if not customer:
            continue
        coupon.status = UserCoupon.UNUSED
        coupon.customer_id = customer.id
        chain = coupon.extras.get('chain')
        if not chain or chain[-1] != to_mama.id:  # 没有　流通过程中的妈妈记录　或者　要退的上级　不是对应的妈妈ｉｄ则抛出异常
            raise Exception('异常优惠券记录')
        chain.pop()
        coupon.extras['chain'] = chain
        coupon.save(update_fields=['status', 'customer_id', 'extras', 'modified'])
        mama_ids.add(transfer.coupon_to_mama_id)
        mama_ids.add(transfer.coupon_from_mama_id)
    for mama_id in mama_ids:
        task_calc_xlmm_elite_score(mama_id)  # 重算积分
    return True


def transfer_coupons(coupons, to_customer_id, transfer_record_id, chain):
    # type: (List[UserCoupon], int, int, List[int])
    """转券
    """
    from .transfercoupondetail import create_transfer_coupon_detail

    coupon_ids = []
    for coupon in coupons:
        coupon.customer_id = to_customer_id
        coupon.extras.update({"transfer_coupon_pk": str(transfer_record_id)})
        if not coupon.extras.has_key('chain'):  # 添加流通的上级妈妈　用于　退券　时候　退回上级
            coupon.extras['chain'] = chain
        else:
            coupon.extras['chain'].extend(chain)
        coupon.save()
        coupon_ids.append(coupon.id)
    create_transfer_coupon_detail(transfer_record_id, coupon_ids)


def unfreeze_user_coupon_by_userbudget(customer_id):
    from flashsale.pay.models import Customer

    customer = Customer.objects.normal_customer.filter(id=customer_id).first()
    if customer:
        from flashsale.coupon.models.usercoupon import UserCoupon

        user_coupons = UserCoupon.objects.filter(customer_id=customer.id, coupon_type=UserCoupon.TYPE_TRANSFER,
                                                 status=UserCoupon.FREEZE)
        if user_coupons and user_coupons.count() > 0:
            for coupon in user_coupons:
                if coupon.extras.has_key("freeze_type") and coupon.extras["freeze_type"] == 1:
                    coupon.extras.pop('freeze_type')
                    coupon.status = UserCoupon.UNUSED
                    coupon.save()

