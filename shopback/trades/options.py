# -*- coding:utf8 -*-
import datetime

from django.db import IntegrityError, transaction
from shopback.trades.models import (MergeTrade,
                                    MergeOrder,
                                    MergeBuyerTrade)
from shopback import paramconfig as pcfg
from django.db import transaction
from core.options import log_action, ADDITION, CHANGE
from shopback.signals import recalc_fee_signal
from common.utils import update_model_fields, cache_lock
import logging

logger = logging.getLogger('django.request')


class MergeException(Exception):
    pass


def _createAndCalcOrderFee(trade, sub_trade):
    payment = 0
    total_fee = 0
    discount_fee = 0
    adjust_fee = 0
    for order in sub_trade.merge_orders.all():

        merge_order, state = MergeOrder.objects.get_or_create(
            oid=order.oid,
            merge_trade=trade)
        for field in order._meta.fields:
            if field.name not in ('id', 'oid', 'merge_trade'):
                setattr(merge_order, field.name, getattr(order, field.name))
        if state:
            merge_order.is_merge = state
        if MergeOrder.NORMAL in (order.sys_status, merge_order.sys_status):
            merge_order.sys_status = MergeOrder.NORMAL
        else:
            merge_order.sys_status = MergeOrder.DELETE
        merge_order.is_reverse_order = trade.isPostScan()
        merge_order.created = order.created
        merge_order.pay_time = order.pay_time
        merge_order.save()

        if order.isEffect():
            payment += order.payment
            total_fee += order.total_fee
            discount_fee += order.discount_fee
            adjust_fee += order.adjust_fee

    trade.payment += payment
    trade.total_fee += total_fee
    trade.discount_fee += discount_fee
    trade.adjust_fee += adjust_fee
    trade.post_fee = sub_trade.post_fee + trade.post_fee

    update_model_fields(trade, update_fields=['payment',
                                              'total_fee',
                                              'discount_fee',
                                              'adjust_fee',
                                              'post_fee'])


@cache_lock(cache_time=12 * 60 * 60)
@transaction.atomic
def mergeMaker(trade, sub_trade):
    if not isinstance(trade, MergeTrade):
        trade = MergeTrade.objects.get(id=trade)

    if not isinstance(sub_trade, MergeTrade):
        sub_trade = MergeTrade.objects.get(id=sub_trade)

    if MergeBuyerTrade.objects.filter(sub_tid=trade.id).count() > 0:
        return False

    try:
        mt = MergeBuyerTrade.objects.get(sub_tid=sub_trade.id)
    except:
        MergeBuyerTrade.objects.get_or_create(sub_tid=sub_trade.id,
                                              main_tid=trade.id)
    else:
        mt.main_tid = trade.id
        mt.save()

    trade.append_reason_code(pcfg.MULTIPLE_ORDERS_CODE)

    if (not trade.is_locked and
                trade.sys_status == pcfg.WAIT_PREPARE_SEND_STATUS):
        trade.sys_status = pcfg.WAIT_AUDIT_STATUS
        update_model_fields(trade, update_fields=['sys_status'])

    _createAndCalcOrderFee(trade, sub_trade)

    if sub_trade.buyer_message or sub_trade.seller_memo or sub_trade.sys_memo:
        trade.update_buyer_message(sub_trade.id,
                                   sub_trade.buyer_message)
        trade.update_seller_memo(sub_trade.id,
                                 sub_trade.seller_memo + sub_trade.sys_memo)
        trade.append_reason_code(pcfg.NEW_MEMO_CODE)

    if sub_trade.has_merge:
        strades = MergeBuyerTrade.objects.filter(main_tid=sub_trade.id)

        for strade in strades:
            MergeBuyerTrade.objects.filter(sub_tid=strade.sub_tid).update(main_tid=trade.id)

        MergeOrder.objects.filter(merge_trade=sub_trade.id, is_merge=True).delete()

    for scode in sub_trade.reason_code.split(','):
        trade.append_reason_code(scode)

    sub_trade.append_reason_code(pcfg.NEW_MERGE_TRADE_CODE)

    # 判断是否还有订单需要合并,如果没有，则去掉需合单问题编号
    queryset = MergeTrade.objects.getMergeQueryset(trade.buyer_nick,
                                                   trade.receiver_name,
                                                   trade.receiver_mobile,
                                                   trade.receiver_phone, )

    if (trade.type == MergeTrade.WX_TYPE
        or queryset.filter(sys_status__in=(pcfg.WAIT_AUDIT_STATUS,
                                           pcfg.REGULAR_REMAIN_STATUS)) \
                .exclude(id__in=(sub_trade.id, trade.id)).count() == 0):
        trade.remove_reason_code(pcfg.MULTIPLE_ORDERS_CODE)

    log_action(trade.user.user.id, trade, CHANGE,
               u'合并订单（%s）' % (sub_trade.id))

    if (not trade.reason_code and
            not trade.is_locked and
                trade.sys_status == pcfg.WAIT_AUDIT_STATUS):
        trade.sys_status = pcfg.WAIT_PREPARE_SEND_STATUS
    else:
        trade.append_reason_code(pcfg.NEW_MERGE_TRADE_CODE)

    log_action(sub_trade.user.user.id, sub_trade, CHANGE,
               u'并入订单（%s）' % (trade.id))

    sub_trade.sys_status = pcfg.ON_THE_FLY_STATUS
    update_model_fields(sub_trade, update_fields=['sys_status'])

    trade.has_merge = True
    update_model_fields(trade, update_fields=['has_merge', 'sys_status'])

    return True


@cache_lock(cache_time=12 * 60 * 60)
@transaction.atomic
def mergeRemover(trade):
    from shopapp.memorule.services import ruleMatchPayment

    if not isinstance(trade, MergeTrade):
        trade = MergeTrade.objects.get(id=trade)

    trade_id = trade.id
    if not trade.has_merge:
        return False

    trade.remove_reason_code(pcfg.NEW_MERGE_TRADE_CODE)
    trade.has_merge = False

    trade.merge_orders.filter(is_merge=True).delete()
    sub_merges = MergeBuyerTrade.objects.filter(main_tid=trade_id)

    for sub_merge in sub_merges:
        sub_trade = MergeTrade.objects.get(id=sub_merge.sub_tid)
        sub_trade.remove_reason_code(pcfg.NEW_MERGE_TRADE_CODE)

        trade.remove_buyer_message(sub_merge.sub_tid)
        trade.remove_seller_memo(sub_merge.sub_tid)

        sub_trade.sys_status = pcfg.WAIT_AUDIT_STATUS
        update_model_fields(sub_trade, update_fields=['sys_status'])

        log_action(trade.user.user.id, sub_trade, CHANGE, u'取消合并')

        trade.payment -= sub_trade.payment
        trade.post_fee -= sub_trade.post_fee

    update_model_fields(trade, update_fields=['payment', 'post_fee', 'has_merge'])

    mbts = MergeBuyerTrade.objects.filter(main_tid=trade_id)
    for mbt in mbts:
        mbt.delete()

    log_action(trade.user.user.id, trade, CHANGE, u'取消合并')

    recalc_fee_signal.send(sender=MergeTrade, trade_id=trade_id)

    ruleMatchPayment(trade)

    return True


def driveMergeTrade(trade, latest_paytime=None):
    """ 驱动合单程序 """

    if not isinstance(trade, MergeTrade):
        trade = MergeTrade.objects.get(id=trade)

    if (trade.has_merge or
                trade.sys_status not in (pcfg.WAIT_AUDIT_STATUS,
                                         pcfg.REGULAR_REMAIN_STATUS)
        or MergeTrade.objects.isTradeRefunding(trade)):
        return

    trade_id = trade.id
    main_trade = None

    try:
        buyer_nick = trade.buyer_nick  # 买家昵称
        receiver_mobile = trade.receiver_mobile  # 收货手机
        receiver_phone = trade.receiver_phone  # 收货手机
        receiver_name = trade.receiver_name  # 收货人
        receiver_address = trade.receiver_address  # 收货地址
        full_address = trade.buyer_full_address  # 详细地址

        merge_queryset = MergeTrade.objects.getMergeQueryset(
            buyer_nick,
            receiver_name,
            receiver_mobile,
            receiver_phone,
            ware_by=trade.ware_by,
            latest_paytime=latest_paytime)

        scan_merge_trades = merge_queryset.filter(sys_status__in=(
            pcfg.WAIT_CHECK_BARCODE_STATUS,
            pcfg.WAIT_SCAN_WEIGHT_STATUS))
        if scan_merge_trades.count() > 0:
            return

        trades = merge_queryset.filter(
            receiver_address=receiver_address
            , sys_status__in=(
                pcfg.WAIT_AUDIT_STATUS,
                pcfg.WAIT_PREPARE_SEND_STATUS,
                pcfg.REGULAR_REMAIN_STATUS)
            , is_force_wlb=False) \
            .exclude(id=trade_id).order_by('pay_time')

        # 如果有已有合并记录，则将现有主订单作为合并主订单
        has_merge_trades = trades.filter(has_merge=True)
        if has_merge_trades.count() > 0:
            main_trade = has_merge_trades[0]

        if trades.count() > 0:
            if not main_trade:
                for t in trades:
                    if (not MergeTrade.objects.isTradeFullRefund(t.id) and
                            not t.has_refund and
                                t.buyer_full_address == full_address):
                        main_trade = t
                        break

                    if t.has_refund:
                        main_trade = None
                        break
            if main_trade and mergeMaker(main_trade, trade):
                return main_trade
    except Exception, exc:
        logger.error('Merge Trade Error:%s' % exc.message, exc_info=True)

        trade.append_reason_code(pcfg.MERGE_TRADE_ERROR_CODE)
