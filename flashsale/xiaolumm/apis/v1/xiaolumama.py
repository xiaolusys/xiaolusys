# coding=utf-8
from __future__ import unicode_literals, absolute_import

from datetime import timedelta, datetime
from decimal import Decimal

from django.db import transaction
from django.db.models import Q

from core.options import get_systemoa_user
from core.options import log_action, CHANGE
from flashsale.coupon.apis.v1.usercoupon import release_coupon_for_deposit
from flashsale.coupon.models import CouponTransferRecord
from flashsale.pay.apis.v1.customer import get_customer_by_id
from flashsale.pay.models import SaleOrder
from ...models import XiaoluMama
from ...signals import signal_xiaolumama_register_success
from .potentialmama import update_potential_by_deposit, create_potential_mama
from flashsale.xiaolumm import constants as CONS

__ALL__ = [
    'get_mama_by_id',
    'mama_pay_deposit',
    'set_mama_manager_by_mama_id',
    'get_mama_by_openid',
    'change_mama_follow_elite_mama'
]


def get_mama_by_id(id):
    # type: (int) -> XiaoluMama
    return XiaoluMama.objects.get(id=id)


def get_mama_by_openid(openid):
    # type: (text_type) -> XiaoluMama
    return XiaoluMama.objects.get(openid=openid)


def mama_pay_deposit(customer_id, deposit_type, referrer, trade_id, oid=None):
    # type: (int, int, int, int, Optional[text_type]) -> None
    """用户支付押金妈妈记录相关处理
    """
    customer = get_customer_by_id(customer_id)
    xlmm = customer.get_xiaolumm()
    if not xlmm:
        return
    if deposit_type not in [1, 99, 188]:
        return
    if deposit_type == 1:
        renew_days = XiaoluMama.TRIAL
        if not xlmm.is_trialable():
            return  # 不可以试用
        # create_potential_mama(xlmm, referrer)  # 创建潜在妈妈记录
    elif deposit_type == 99:
        renew_days = XiaoluMama.HALF
    elif deposit_type == 188:
        renew_days = XiaoluMama.FULL
    mama_charged = xlmm.chargemama()  # 接管妈妈
    sys_oa = get_systemoa_user()
    if mama_charged:
        log_action(sys_oa, xlmm, CHANGE, u'代理接管成功')
    xlmm.update_renew_day(renew_days)  # 修改下次续费时间
    xlmm.deposit_pay()  # 支付押金
    log_action(sys_oa, xlmm, CHANGE, u'支付押金')
    release_coupon_for_deposit(customer_id, deposit_type, trade_id=trade_id)  # 发送押金优惠券给用户
    update_potential_by_deposit(xlmm.id, renew_days, referrer_mama_id=referrer, oid=oid)  # 更新潜在关系记录
    signal_xiaolumama_register_success.send_robust(sender=XiaoluMama, xiaolumama=xlmm, renew=True)  # 发送信号


def set_mama_manager_by_mama_id(mama_id, manager_id):
    # type : (int, int) -> XiaoluMama
    """修改该妈妈的管理员
    """
    mm = get_mama_by_id(mama_id)

    if mm.manager != manager_id:
        mm.manager = manager_id
        mm.save(update_fields=['manager'])
    return mm


def change_mama_follow_elite_mama(mama_id, upper_mama_id, direct_info):
    # type: (int, int, text_type) -> bool
    """修改推荐关系的上级,修改该妈妈的上级为指定的精英妈妈
    """
    from .relationship import get_relationship_by_mama_id

    mm = get_mama_by_id(mama_id)
    upper_elite_mama = get_mama_by_id(upper_mama_id)

    if upper_elite_mama.last_renew_type < XiaoluMama.ELITE:
        raise Exception('指定的上级妈妈不是精英妈妈')

    relationship = get_relationship_by_mama_id(mm.id)  # 获取当前妈妈的推荐关系
    if not relationship:
        raise Exception('推荐关系没有找到')

    with transaction.atomic():
        if mm.charge_status != XiaoluMama.CHARGED:
            mm.chargemama()  # 没有接管的话 要接管下

        if mm.last_renew_type in [XiaoluMama.TRIAL, XiaoluMama.SCAN]:  # 试用的情况要修改该
            mm.last_renew_type = XiaoluMama.ELITE  # 修改为精英妈妈
        mm.referal_from = direct_info
        mm.save()

        relationship.change_referal_mama(upper_mama_id, is_elite=True)  # 修改该推荐关系的上级
    return True


def xlmm_recharge_cacl_score(price):
    """精英妈妈充值算积分
    """
    score = 0
    if price == 600:
        score = 100
    elif price == 3000:
        score = 600
    elif price == 9000:
        score = 2000
    elif price == 25000:
        score = 6000
    elif price == 80000:
        score = 20000
    return score


def get_xlmm_xiaolu_coin(mamaid):
    from flashsale.xiaolumm.models.xiaolucoin import XiaoluCoin
    coin = XiaoluCoin.objects.filter(mama_id=mamaid).first()
    if coin:
        return coin.xiaolucoin_cash
    else:
        return 0


def current_month_rebate_remain(mama_id):
    """
    精英妈妈, 当前月份距离返点所差购券金额

    return:
    (差多少积分能拿返点, 能拿到多少钱)
    (remain_score, money)
    """
    remain_score = 0
    money = 0

    score, upgrade_date = task_calc_xlmm_elite_score(mama_id)
    min_socre = CONS.ELITEMM_DESC_INFO[CONS.ELITEMM_PARTNER].get('min_score')

    if score < min_socre:
        return (min_socre-score, money)

    today = datetime.today()
    thismonth = datetime(today.year, today.month, 1)
    start_date = thismonth
    end_date = today

    result = get_mama_buy_coupon_score(mama_id, start_date, end_date)
    return (0, result['fd'])


def task_calc_xlmm_elite_score(mama_id):
    """
    计算精英妈妈积分
    """
    if mama_id <= 0:
        return

    records = CouponTransferRecord.objects.filter(
        Q(coupon_from_mama_id=mama_id) | Q(coupon_to_mama_id=mama_id),
        transfer_status=CouponTransferRecord.DELIVERED).order_by('created')

    score = 0
    upgrade_date = None
    for record in records:

        if record.coupon_from_mama_id == mama_id:
            if record.transfer_type in [CouponTransferRecord.OUT_CASHOUT, CouponTransferRecord.IN_RETURN_COUPON]:
                score = score - record.elite_score

        if record.coupon_to_mama_id == mama_id:
            if record.transfer_type in [
                CouponTransferRecord.IN_BUY_COUPON,
                CouponTransferRecord.OUT_TRANSFER,
                CouponTransferRecord.IN_GIFT_COUPON,
                CouponTransferRecord.IN_RECHARGE
            ]:
                score += record.elite_score

        if score >= 3000 and upgrade_date is None:
            upgrade_date = record.created

    return score, upgrade_date


def get_mama_buy_coupon_score(mama_id, start_date, end_date):
    """
    计算精英妈妈购券获得的返点
    """
    score = 0
    payment = 0

    in_records = CouponTransferRecord.objects.filter(
        coupon_to_mama_id=mama_id,
        transfer_status=CouponTransferRecord.DELIVERED,
        transfer_type__in=[
            CouponTransferRecord.IN_BUY_COUPON,
            CouponTransferRecord.IN_BUY_COUPON_WITH_COIN
        ],
        created__gt=start_date,
        created__lt=end_date,
    )

    out_records = CouponTransferRecord.objects.filter(
        coupon_from_mama_id=mama_id,
        transfer_status=CouponTransferRecord.DELIVERED,
        transfer_type__in=[
            CouponTransferRecord.OUT_CASHOUT,
            CouponTransferRecord.OUT_CASHOUT_COIN
        ],
        created__gt=start_date,
        created__lt=end_date,
    )

    for record in in_records:
        order_id = record.order_no
        try:
            order = SaleOrder.objects.get(oid=order_id)
        except Exception:
            continue
        payment += order.payment
        print '+', order.payment, record.transfer_type

    for record in out_records:
        try:
            _, _, money = record.order_no.split('-')
        except Exception, e:
            print e
            continue
        payment -= float(money)
        print '-', money, record.transfer_type


    fd = 0
    if 10000 <= payment < 20000:
        fd = payment * 0.01
    elif 20000 <= payment < 50000:
        fd = payment * 0.02
    elif 50000 <= payment < 100000:
        fd = payment * 0.03
    elif 100000 <= payment < 150000:
        fd = payment * 0.05
    elif 150000 <= payment < 200000:
        fd = payment * 0.06
    elif 200000 <= payment < 300000:
        fd = payment * 0.07
    elif 300000 <= payment < 400000:
        fd = payment * 0.08
    elif 400000 <= payment < 500000:
        fd = payment * 0.09
    elif payment >= 500000:
        fd = payment * 0.10

    return {'score': score, 'payment': payment, 'fd': fd, 'start_date': start_date, 'end_date': end_date}
