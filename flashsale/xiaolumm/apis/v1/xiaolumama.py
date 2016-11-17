# coding=utf-8
from __future__ import unicode_literals, absolute_import

__ALL__ = [
    'mama_pay_deposit',
]

from core.options import get_systemoa_user
from core.options import log_action, CHANGE
from flashsale.coupon.apis.v1.usercoupon import release_coupon_for_deposit
from flashsale.pay.apis.v1.customer import get_customer_by_id
from ...models import XiaoluMama
from ...signals import signal_xiaolumama_register_success
from .potentialmama import update_potential_by_deposit, create_potential_mama


def mama_pay_deposit(customer_id, deposit_type, referrer, oid=None):
    # type: (int, int, int, Optional[text_type]) -> None
    """用户支付押金妈妈记录相关处理
    """
    customer = get_customer_by_id(customer_id)
    xlmm = customer.get_xiaolumm()
    if not xlmm:
        return
    if deposit_type not in [1, 99, 188]: return

    mama_charged = xlmm.chargemama()  # 接管妈妈
    sys_oa = get_systemoa_user()
    if mama_charged:
        log_action(sys_oa, xlmm, CHANGE, u'代理接管成功')
    if deposit_type == 1:
        renew_days = XiaoluMama.TRIAL
        if not xlmm.is_trialable(): return  # 不可以试用
        create_potential_mama(xlmm, referrer)  # 创建潜在妈妈记录
    elif deposit_type == 99:
        renew_days = XiaoluMama.HALF
    elif deposit_type == 188:
        renew_days = XiaoluMama.FULL
    xlmm.update_renew_day(renew_days)  # 修改下次续费时间
    xlmm.deposit_pay()  # 支付押金
    log_action(sys_oa, xlmm, CHANGE, u'支付押金')
    release_coupon_for_deposit(customer_id, deposit_type)  # 发送押金优惠券给用户
    update_potential_by_deposit(xlmm.id, referrer, renew_days, oid=oid)  # 更新潜在关系记录
    signal_xiaolumama_register_success.send_robust(sender=XiaoluMama, xiaolumama=xlmm, renew=True)  # 发送信号
