# -*- coding:utf8 -*-
from django.conf import settings
from .handler import BaseHandler
from shopback.trades.models import MergeTrade, MergeBuyerTrade
from shopback import paramconfig as pcfg
from core.options import log_action, User, ADDITION, CHANGE
from common.modelutils import update_model_fields

import logging

logger = logging.getLogger('celery.handler')


class MemoHandler(BaseHandler):
    def getOriginMemo(self, merge_trade, origin_trade):

        if hasattr(origin_trade, 'memo'):
            return origin_trade.memo
        elif hasattr(origin_trade, 'seller_memo'):
            return origin_trade.seller_memo
        elif hasattr(origin_trade, 'vender_remark'):
            return origin_trade.vender_remark
        else:
            return merge_trade.seller_memo

    def getOriginBuyerMessage(self, merge_trade, origin_trade):

        if hasattr(origin_trade, 'buyer_message'):
            return origin_trade.buyer_message
        elif hasattr(origin_trade, 'supplier_memo'):
            return origin_trade.supplier_memo
        elif hasattr(origin_trade, 'order_remark'):
            return origin_trade.order_remark
        else:
            return merge_trade.buyer_message

    def handleable(self, merge_trade, *args, **kwargs):

        origin_trade = kwargs.get('origin_trade', None)

        seller_memo = self.getOriginMemo(merge_trade, origin_trade).strip()
        buyer_message = self.getOriginBuyerMessage(merge_trade, origin_trade).strip()

        has_memo = seller_memo or buyer_message
        new_memo = has_memo and (merge_trade.buyer_message != buyer_message
                                 or merge_trade.seller_memo != seller_memo)

        return new_memo or (kwargs.get('first_pay_load', None) and has_memo)

    def process(self, merge_trade, *args, **kwargs):

        logger.debug('DEBUG MEMO:%s' % merge_trade)

        origin_trade = kwargs.get('origin_trade', None)

        merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)

        merge_trade.seller_memo = self.getOriginMemo(merge_trade, origin_trade)
        merge_trade.buyer_message = self.getOriginBuyerMessage(merge_trade, origin_trade)

        update_model_fields(merge_trade, update_fields=['seller_memo',
                                                        'buyer_message'])

        log_action(merge_trade.user.user.id,
                   merge_trade, ADDITION,
                   u'订单备注:[%s:%s]' % (merge_trade.buyer_message,
                                      merge_trade.seller_memo))

        merge_type = MergeBuyerTrade.getMergeType(merge_trade.id)

        if merge_type == pcfg.SUB_MERGE_TYPE:
            mbt = MergeBuyerTrade.objects.get(sub_tid=merge_trade.id)

            main_trade = MergeTrade.objects.get(id=mbt.main_tid)
            main_trade.append_reason_code(pcfg.NEW_MEMO_CODE)

            main_trade.update_buyer_message(merge_trade.id,
                                            merge_trade.buyer_message)

            main_trade.update_seller_memo(merge_trade.id,
                                          merge_trade.seller_memo)
