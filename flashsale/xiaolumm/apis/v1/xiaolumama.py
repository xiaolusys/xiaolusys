# coding=utf-8
from __future__ import unicode_literals, absolute_import
from django.db import transaction
from core.options import get_systemoa_user
from core.options import log_action, CHANGE
from flashsale.coupon.apis.v1.usercoupon import release_coupon_for_deposit
from flashsale.pay.apis.v1.customer import get_customer_by_id
from ...models import XiaoluMama
from ...signals import signal_xiaolumama_register_success
from .potentialmama import update_potential_by_deposit, create_potential_mama

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
        create_potential_mama(xlmm, referrer)  # 创建潜在妈妈记录
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
