# -*- coding: utf-8 -*-

from shopback import paramconfig as pcfg
from shopback.items.models import Product
from shopback.trades.models import MergeTrade, MergeOrder
from common.utils import update_model_fields
from shopback.users.models import User
from core.options import log_action, User as DjangoUser, ADDITION, CHANGE
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_CHOICES


def releaseRegularOutstockTrade(trade, num_maps=None):
    """ 释放特卖定时订单 """
    trade_out_stock = False
    full_out_stock = True
    tnum_maps = {}
    ware_set = set()
    code_defect = False

    for order in trade.normal_orders:
        try:
            bar_code = order.outer_id + order.outer_sku_id
            tnum_maps[bar_code] = tnum_maps.get(bar_code, 0) + order.num
            plus_num = num_maps.get(bar_code, 0) + tnum_maps[bar_code]
            out_stock = not Product.objects.isProductOutingStockEnough(
                order.outer_id,
                order.outer_sku_id,
                plus_num)
            order.out_stock = out_stock
            order.save()
            trade_out_stock |= out_stock
            full_out_stock &= out_stock
            prduct_ware = Product.objects.get(outer_id=order.outer_id).ware_by
            ware_set.add(prduct_ware)
        except Product.ProductCodeDefect:
            code_defect = True
            continue

    t = MergeTrade.objects.get(id=trade.id)
    if trade_out_stock:
        t.append_reason_code(pcfg.OUT_GOOD_CODE)

    if len(ware_set) == 1:
        t.ware_by = ware_set.pop()
    else:
        t.ware_by = WARE_NONE
        t.sys_memo += u'[物流：请拆单或选择始发仓]'
        t.append_reason_code(pcfg.DISTINCT_RULE_CODE)

    if t.reason_code:
        if not code_defect and full_out_stock:
            t.sys_status = pcfg.REGULAR_REMAIN_STATUS
        else:
            t.sys_status = pcfg.WAIT_AUDIT_STATUS
            for code, num in tnum_maps.iteritems():
                num_maps[code] = num_maps.get(code, 0) + num
    else:
        t.sys_status = pcfg.WAIT_PREPARE_SEND_STATUS
    update_model_fields(t, update_fields=['sys_status', 'sys_memo', 'ware_by'])

    if t.sys_status in (pcfg.WAIT_AUDIT_STATUS, pcfg.WAIT_PREPARE_SEND_STATUS):
        oauser = User.getSystemOAUser()
        log_action(oauser.id, t, CHANGE, u'到货释放订单')
    return t


from common.cachelock import cache_lock


@cache_lock(cache_time=6 * 60 * 60)
def releaseProductTrades(outer_id):
    """ 释放特卖到货商品订单 """
    products = Product.objects.filter(outer_id=outer_id)
    if not products.exists() or not products[0].has_quantity():
        return

    mos = (MergeOrder.objects.filter(
        outer_id=outer_id,
        sys_status=MergeOrder.NORMAL,
        merge_trade__sys_status=pcfg.REGULAR_REMAIN_STATUS)
           .order_by('merge_trade__prod_num', 'merge_trade__has_merge'))

    num_maps = {}
    merge_trades = set([o.merge_trade for o in mos])
    for trade in merge_trades:
        releaseRegularOutstockTrade(trade, num_maps)
