# -*- coding:utf-8 -*-
from django.conf import settings
from django.db.models.signals import post_save

from core.options import log_action, User, ADDITION, CHANGE
from shopback.trades.models import MergeTrade, MergeOrder, MergeBuyerTrade
from shopback.items.models import Product
from shopback.signals import confirm_trade_signal
from shopback import paramconfig as pcfg
from common.utils import update_model_fields
from shopback.warehouse import WARE_NONE, WARE_GZ, WARE_SH, WARE_CHOICES
import logging

logger = logging.getLogger("celery.handler")
OUT_STOCK_KEYWORD = [u'到', u'预售']


class BaseHandler(object):
    def handleable(self, *args, **kwargs):
        raise Exception('Not Implement.')

    def process(self, *args, **kwargs):
        raise Exception('Not Implement.')


class ConfirmHandler(BaseHandler):
    def handleable(self, merge_trade, *args, **kwargs):
        return merge_trade.status == pcfg.TRADE_FINISHED

    def process(self, merge_trade, *args, **kwargs):

        try:
            confirm_trade_signal.send(sender=MergeTrade,
                                      trade_id=merge_trade.id)
        except:
            pass


class InitHandler(BaseHandler):
    def handleable(self, merge_trade, *args, **kwargs):
        return kwargs.get('first_pay_load', None)

    def process(self, merge_trade, *args, **kwargs):
        logger.debug('DEBUG INIT:%s' % merge_trade)
        log_action(merge_trade.user.user.id,
                   merge_trade, ADDITION,
                   u'订单入库')

        merge_trade.ware_by = merge_trade.get_trade_assign_ware()
        merge_trade.sys_status = pcfg.REGULAR_REMAIN_STATUS
        if merge_trade.ware_by == WARE_NONE:
            merge_trade.sys_memo += '，请选择所属仓库'
            merge_trade.append_reason_code(pcfg.NEW_MEMO_CODE)

        update_model_fields(merge_trade, update_fields=['sys_status', 'ware_by', 'sys_memo'])


class StockOutHandler(BaseHandler):
    def handleable(self, merge_trade, *args, **kwargs):
        return (kwargs.get('first_pay_load', None) and
                MergeTrade.objects.isTradeOutStock(merge_trade))

    def isOutStockByTitle(self, order):

        for kw in OUT_STOCK_KEYWORD:
            try:
                ('%s%s'(order.title, order.sku_properties_name)).index(kw)
            except:
                pass
            else:
                return True
        return False

    def process(self, merge_trade, *args, **kwargs):

        logger.debug('DEBUG STOCKOUT:%s' % merge_trade)

        merge_trade.append_reason_code(pcfg.OUT_GOOD_CODE)
        for order in merge_trade.inuse_orders:
            if Product.objects.isProductOutOfStock(order.outer_id,
                                                   order.outer_sku_id) or \
                    self.isOutStockByTitle(order):
                order.out_stock = True
                update_model_fields(order, update_fields=['out_stock'])

        post_save.send(sender=MergeOrder, instance=order)


class DefectHandler(BaseHandler):
    def handleable(self, merge_trade, *args, **kwargs):
        return (kwargs.get('first_pay_load', None) and
                MergeTrade.objects.isTradeDefect(merge_trade))

    def process(self, merge_trade, *args, **kwargs):

        logger.debug('DEBUG DEFECT:%s' % merge_trade)

        merge_trade.append_reason_code(pcfg.TRADE_DEFECT_CODE)

        for order in merge_trade.inuse_orders:
            if MergeTrade.objects.isOrderDefect(order.outer_id,
                                                order.outer_sku_id):
                order.is_rule_match = True
                update_model_fields(order, update_fields=['is_rule_match'])

        post_save.send(sender=MergeOrder, instance=order)


class RuleMatchHandler(BaseHandler):
    def handleable(self, merge_trade, *args, **kwargs):
        return (kwargs.get('first_pay_load', None) and
                MergeTrade.objects.isTradeRuleMatch(merge_trade))

    def process(self, merge_trade, *args, **kwargs):

        logger.debug('DEBUG RULE MATCH:%s' % merge_trade)

        merge_trade.append_reason_code(pcfg.RULE_MATCH_CODE)
        match_reason_list = []

        for order in merge_trade.inuse_orders:
            if MergeTrade.objects.isOrderRuleMatch(order):
                order.is_rule_match = True
                update_model_fields(order, update_fields=['is_rule_match'])
                match_reason_list.append(
                    Product.objects.getProductMatchReason(order.outer_id,
                                                          order.outer_sku_id))

        merge_trade.sys_memo = u'%s,匹配原因:%s' % (merge_trade.sys_memo,
                                                ','.join(match_reason_list))

        update_model_fields(merge_trade, update_fields=['sys_memo'])

        post_save.send(sender=MergeOrder, instance=order)


class FinalHandler(BaseHandler):
    def handleable(self, *args, **kwargs):
        return True

    def process(self, merge_trade, *args, **kwargs):

        logger.debug('DEBUG FINAL:%s' % merge_trade)

        if (merge_trade.sys_status != pcfg.EMPTY_STATUS and
                not merge_trade.logistics_company):
            merge_trade.append_reason_code(pcfg.LOGISTIC_ERROR_CODE)

        if (merge_trade.logistics_company and
                merge_trade.has_reason_code(pcfg.LOGISTIC_ERROR_CODE)):
            merge_trade.remove_reason_code(pcfg.LOGISTIC_ERROR_CODE)

        if ((merge_trade.reason_code and not merge_trade.is_locked and
                     merge_trade.sys_status == pcfg.WAIT_PREPARE_SEND_STATUS) or
                (merge_trade.sys_status == pcfg.REGULAR_REMAIN_STATUS and
                         merge_trade.remind_time == None)):
            merge_trade.sys_status = pcfg.WAIT_AUDIT_STATUS

        if (not merge_trade.reason_code and
                (merge_trade.sys_status == pcfg.WAIT_AUDIT_STATUS
                 or (merge_trade.sys_status == pcfg.REGULAR_REMAIN_STATUS
                     and merge_trade.remind_time == None))
            and merge_trade.type not in (pcfg.DIRECT_TYPE,
                                         pcfg.EXCHANGE_TYPE,
                                         pcfg.REISSUE_TYPE)):
            merge_trade.sys_status = pcfg.WAIT_PREPARE_SEND_STATUS

        if kwargs.get('first_pay_load', None):
            for order in merge_trade.inuse_orders:
                ### we should comment the following line in order to retire updating waitpostnum
                Product.objects.updateWaitPostNumByCode(order.outer_id,
                                                        order.outer_sku_id,
                                                        order.num)

        if (merge_trade.status in (pcfg.TRADE_FINISHED,
                                   pcfg.TRADE_BUYER_SIGNED,
                                   pcfg.TRADE_CLOSED,
                                   pcfg.TRADE_CLOSED_BY_TAOBAO) and
                    merge_trade.sys_status not in (pcfg.FINISHED_STATUS,
                                                   pcfg.INVALID_STATUS)):
            merge_trade.append_reason_code(pcfg.INVALID_END_CODE)

            if not merge_trade.is_locked:

                merge_type = MergeBuyerTrade.getMergeType(merge_trade.id)

                if merge_type == pcfg.SUB_MERGE_TYPE:
                    main_tid = MergeBuyerTrade.objects.get(
                        sub_tid=merge_trade.id).main_tid

                    main_trade = MergeTrade.objects.get(id=main_tid)
                    main_trade.append_reason_code(pcfg.INVALID_END_CODE)

                    sub_oids = [o[0] for o in merge_trade.merge_orders.values_list('oid')]
                    main_trade.merge_orders.filter(oid__in=sub_oids) \
                        .update(sys_status=pcfg.INVALID_STATUS)

                elif merge_type == pcfg.MAIN_MERGE_TYPE:
                    MergeTrade.objects.mergeRemover(merge_trade.id)

                merge_trade.sys_status = pcfg.INVALID_STATUS

        update_model_fields(merge_trade, update_fields=['sys_status'])
