# -*- coding:utf8 -*-
from django.conf import settings
from .handler import BaseHandler

from shopback.trades.models import MergeTrade,MergeOrder,MergeBuyerTrade
from shopapp.memorule.services import ruleMatchPayment,ruleMatchSplit

from shopback import paramconfig as pcfg
from common.modelutils import update_model_fields

import logging
logger = logging.getLogger('celery.handler')


class RefundHandler(BaseHandler):
    def handleable(self, merge_trade, *args, **kwargs):
        return (MergeTrade.objects.isTradeFullRefund(merge_trade) or
                MergeTrade.objects.isTradeNewRefund(merge_trade))

    def atWAIT_BUYER_CONFIRM_GOODS(self, merge_trade):

        merge_type = MergeBuyerTrade.getMergeType(merge_trade.id)
        # 如果有合并的父订单，则设置父订单退款编号
        if merge_type == pcfg.SUB_MERGE_TYPE:
            main_tid = MergeBuyerTrade.objects.get(sub_tid=merge_trade.id).main_tid
            MergeTrade.objects.get(id=main_tid).append_reason_code(pcfg.NEW_REFUND_CODE)
            main_trade = MergeTrade.objects.get(id=main_tid)
            main_order = None
            for order in merge_trade.merge_orders.all():
                main_order = main_trade.merge_orders.get(oid=order.oid)
                main_order.status = order.status
                main_order.refund_status = order.refund_status
                main_order.sys_status = order.sys_status
                update_model_fields(main_order, update_fields=['status',
                                                               'refund_status',
                                                               'sys_status'])
            if main_order:
                ruleMatchSplit(main_trade)
                ruleMatchPayment(main_trade)

        if (merge_trade.sys_status in pcfg.WAIT_DELIVERY_STATUS and
                not merge_trade.is_locked):
            merge_trade.sys_status = pcfg.INVALID_STATUS

    def atTRADE_CLOSED(self, merge_trade):

        merge_type = MergeBuyerTrade.getMergeType(merge_trade.id)
        if merge_type == pcfg.SUB_MERGE_TYPE:
            mbt = MergeBuyerTrade.objects.get(sub_tid=merge_trade.id)
            MergeTrade.objects.get(id=mbt.main_tid).append_reason_code(pcfg.NEW_REFUND_CODE)

        elif merge_type == pcfg.MAIN_MERGE_TYPE:
            if merge_trade.sys_status not in (pcfg.WAIT_CHECK_BARCODE_STATUS,
                                              pcfg.WAIT_SCAN_WEIGHT_STATUS,
                                              pcfg.FINISHED_STATUS):
                MergeTrade.objects.mergeRemover(merge_trade.id)

    def atWAIT_SELLER_SEND_GOODS(self, merge_trade):

        merge_type = MergeBuyerTrade.getMergeType(merge_trade.id)
        if (merge_type == pcfg.NO_MERGE_TYPE):
            if (not merge_trade.is_locked and
                        merge_trade.sys_status == pcfg.WAIT_PREPARE_SEND_STATUS):
                merge_trade.sys_status = pcfg.WAIT_AUDIT_STATUS

        elif merge_type == pcfg.SUB_MERGE_TYPE:
            main_tid = MergeBuyerTrade.objects.get(
                sub_tid=merge_trade.id).main_tid
            remove_succes = MergeTrade.objects.mergeRemover(main_tid)
            if remove_succes:
                merge_trade.sys_status = pcfg.WAIT_AUDIT_STATUS
        else:
            MergeTrade.objects.mergeRemover(merge_trade.id)

    def update_trade_refund_status(self, merge_trade):

        merge_trade.has_refund = True
        merge_trade.append_reason_code(pcfg.NEW_REFUND_CODE)
        if merge_trade.sys_status in pcfg.WAIT_DELIVERY_STATUS:
            self.atWAIT_SELLER_SEND_GOODS(merge_trade)
        elif merge_trade.sys_status == pcfg.INVALID_STATUS:
            self.atTRADE_CLOSED(merge_trade)
        elif merge_trade.sys_status in pcfg.WAIT_SCAN_CHECK_WEIGHT:
            self.atWAIT_BUYER_CONFIRM_GOODS(merge_trade)
        update_model_fields(merge_trade, update_fields=['has_refund'])

    def process(self, merge_trade, *args, **kwargs):
        """ １，如果初次入库退款，并且有待退款订单，则追加问题编号;
            ２，如果没有无效的退款明细或未分单，正常退款单处理;
            ３，否则按分单发货处理;
        """
        logger.debug('DEBUG REFUND:%s' % merge_trade)

        if (kwargs.get('first_pay_load', None) and
                MergeTrade.objects.isTradeRefunding(merge_trade)):
            merge_trade.append_reason_code(pcfg.WAITING_REFUND_CODE)

        if merge_trade.is_part_consign:
            refund_orders = merge_trade.merge_orders.exclude(refund_status=pcfg.NO_REFUND)
            for order in refund_orders:
                match_orders = (MergeOrder.objects.filter(oid=order.oid,
                                                          merge_trade__user=merge_trade.user,
                                                          sys_status=pcfg.IN_EFFECT)
                                .exclude(merge_trade=merge_trade))
                for mo in match_orders:
                    if mo.refund_status == order.refund_status:
                        continue
                    mo.refund_status = order.refund_status
                    mo.save()

                    mt = order.merge_trade
                    mt.append_reason_code(pcfg.WAITING_REFUND_CODE)

        self.update_trade_refund_status(merge_trade)
