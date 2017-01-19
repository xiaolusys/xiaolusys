# coding=utf-8
import datetime
import re

from flashsale.restpro import constants as CONS
from ...models import SaleOrder


def get_user_skunum_by_last24hours(user, sku):
    # type: (Customer, ProductSku) -> int
    """ 获取用户过去48小时拍下商品规格数量 """
    last_48hour = datetime.datetime.now() - datetime.timedelta(days=2)
    order_nums = SaleOrder.objects.filter(
        buyer_id=user.id,
        sku_id=sku.id,
        status__in=(SaleOrder.WAIT_BUYER_PAY,
                    SaleOrder.WAIT_SELLER_SEND_GOODS,
                    SaleOrder.WAIT_BUYER_CONFIRM_GOODS),
        refund_status=0,
        pay_time__gte=last_48hour).values_list('num', flat=True)
    return sum(order_nums)


def parse_entry_params(pay_extras):
    """
    解析 pay_extras

    示例
    pid:1:value:2,pid:2:couponid:305463/305463/305463:value:50.00,pid:3:budget:46.00
    pid:1:value:2;pid:2:value:3:conponid:2
    """

    if not pay_extras:
        return []

    pay_list = [e for e in re.split(',|;', pay_extras) if e.strip()]
    extra_list = []
    already_exists_pids = []

    for k in pay_list:
        pdict = {}
        keys = k.split(':')
        for i in range(0, len(keys) / 2):
            pdict.update({keys[2 * i]: keys[2 * i + 1]})

        if pdict.get('pid') and pdict['pid'] not in already_exists_pids:
            extra_list.append(pdict)
            already_exists_pids.append(pdict['pid'])
    return extra_list


def parse_pay_extras_to_dict(pay_extras):
    """
    [{'pid': 1, 'value': 2}] => {1: {'pid':1, 'value': 2}}
    """
    extra_list = parse_entry_params(pay_extras)
    d = {}
    for item in extra_list:
        d[item['pid']] = item
    return d


def parse_coupon_ids_from_pay_extras(pay_extras):
    """
    从pay_extras获取优惠券id
    """
    extras = parse_pay_extras_to_dict(pay_extras)
    couponid_str = extras.get(CONS.ETS_COUPON, {}).get('couponid', '')
    coupon_ids = couponid_str.split('/')
    coupon_ids = filter(lambda x: x, coupon_ids)
    return coupon_ids


def get_pay_type_from_trade(sale_trade):
    pay_extras = sale_trade.extras_info.get('pay_extras')
    extras = parse_pay_extras_to_dict(pay_extras)
    budget_value = extras.get(CONS.ETS_BUDGET, {}).get('value', 0)
    coin_value = extras.get(CONS.ETS_XIAOLUCOIN, {}).get('value', 0)

    return float(budget_value) > 0, float(coin_value) > 0
