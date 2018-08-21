# coding=utf-8
from __future__ import unicode_literals, absolute_import
import datetime
import logging
from django.db import transaction
from core.options import log_action, CHANGE, ADDITION
from flashsale.pay.models import BudgetLog
from ...models import CashOut
from .mamafortune import get_mama_fortune_by_mama_id

logger = logging.getLogger(__name__)

__ALL__ = [
    'cash_out_2_budget'
]


def _verify_mama_cash_out(mama):
    # type: (XiaoluMama) -> None
    """校验妈妈是否可以提现
    """
    if not mama.is_cashoutable():
        raise Exception('只有正式妈妈会员才可使用此功能')


def _verify_mama_active_value(mama_fortune):
    # type: (MamaFortune) -> None
    """校验妈妈活跃值是否足够提现条件
    """
    active_value_num = mama_fortune.active_value_num if mama_fortune else 0
    if active_value_num < 100:
        raise Exception('活跃值不足,不能提现')


def _verify_could_gen_cash_out(mama):
    # type: (XiaoluMama) -> None
    """如果有待审核提现记录则不予再次创建记录
    """
    if CashOut.objects.filter(status=CashOut.PENDING, xlmm=mama.id).count() > 0:
        raise Exception('您有提现等待审核,请稍后再试')


def _verify_cash_out_value(mama_fortune, value):
    # type: (MamaFortune, int) -> None
    """校验提现金额
    """
    could_cash_out = mama_fortune.cash_num_display() if mama_fortune else 0
    if could_cash_out < value * 0.01:  # 如果可以提现金额不足
        raise Exception('余额不足!')
    elif value <= 0:
        raise Exception('提现金额不能小于0!')


def _verify_cash_out_2_budget(mama, value):
    # type: (XiaoluMama, int) -> None
    """校验
    """
    mama_fortune = get_mama_fortune_by_mama_id(mama.id)
    _verify_mama_cash_out(mama)
    _verify_could_gen_cash_out(mama)
    _verify_cash_out_value(mama_fortune, value)
    return


def cash_out_2_budget(mama, value):
    # type: (XiaoluMama, int) -> None
    """妈妈钱包 提现到 小鹿钱包
    """
    if not isinstance(value, int):
        raise Exception('参数错误!')
    _verify_cash_out_2_budget(mama, value)
    customer = mama.get_customer()

    with transaction.atomic():
        cashout = CashOut.create(mama.id, value, CashOut.USER_BUDGET)
        cashout.approve_cashout()
        BudgetLog.create_mm_cash_out_2_budget(customer.id, value, cashout.id)

    log_action(customer.user.id, cashout, ADDITION, '代理提现到余额')
