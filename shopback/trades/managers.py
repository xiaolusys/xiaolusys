# -*- coding:utf8 -*-
from django.db import models
from django.db.models import Q, Sum

from core.managers import BaseManager
from shopback import paramconfig as pcfg
from shopback.items.models import Product, ProductSku
from common.utils import update_model_fields


class MergeTradeManager(BaseManager):
    def getMergeQueryset(self, buyer_nick,
                         receiver_name,
                         receiver_mobile,
                         receiver_phone,
                         state='',
                         city='',
                         ware_by=None,
                         latest_paytime=None):
        q = None
        if receiver_mobile:
            if q:
                q = q | Q(receiver_mobile=receiver_mobile)
            else:
                q = Q(receiver_mobile=receiver_mobile)
                #         if receiver_phone:
                #             if q:
                #                 q = q|Q(receiver_phone=receiver_phone)
                #             else:
                #                 q = Q(receiver_phone=receiver_phone)

        if not q:
            return self.none()

        queryset = self.get_queryset().filter(q)
        queryset = queryset.filter(sys_status__in=pcfg.WAIT_WEIGHT_STATUS)

        if state and city:
            queryset = queryset.filter(receiver_state=state, receiver_city=city)
        if ware_by:
            queryset = queryset.filter(ware_by=ware_by)
        if latest_paytime:
            queryset = queryset.filter(pay_time__gte=latest_paytime)

        return queryset

    def getMainMergeTrade(self, trade):

        merge_queryset = self.getMergeQueryset(
            trade.buyer_nick,
            trade.receiver_name,
            trade.receiver_mobile,
            trade.receiver_phone) \
            .filter(has_merge=True)
        if merge_queryset.count() > 0:
            return merge_queryset[0]
        return None

    def mergeMaker(self, trade, sub_trade):

        from shopback.trades.options import mergeMaker
        return mergeMaker(trade, sub_trade)

    def mergeRemover(self, trade):

        from shopback.trades.options import mergeRemover
        return mergeRemover(trade)

    def driveMergeTrade(self, trade, **kwargs):

        from shopback.trades.options import driveMergeTrade
        return driveMergeTrade(trade, **kwargs)

    def updateWaitPostNum(self, trade, **kwargs):

        for order in trade.inuse_orders:

            if self.isOrderDefect(order.outer_id,
                                  order.outer_sku_id):
                continue

            Product.objects.updateWaitPostNumByCode(order.outer_id,
                                                    order.outer_sku_id,
                                                    order.num)

    def reduceWaitPostNum(self, trade):

        for order in trade.inuse_orders:

            if self.isOrderDefect(order.outer_id,
                                  order.outer_sku_id):
                continue

            Product.objects.reduceWaitPostNumByCode(order.outer_id,
                                                    order.outer_sku_id,
                                                    order.num)

    def isOrderDefect(self, outer_id, outer_sku_id):

        try:
            if outer_sku_id:
                ProductSku.objects.get(outer_id=outer_sku_id,
                                       product__outer_id=outer_id)
            else:
                product = Product.objects.get(outer_id=outer_id)
                if product.prod_skus.count() > 0:
                    return True
        except (Product.DoesNotExist, ProductSku.DoesNotExist):
            return True
        return False

    def isTradeDefect(self, trade):

        for order in trade.inuse_orders:
            if self.isOrderDefect(order.outer_id,
                                  order.outer_sku_id):
                return True

        return False

    def isTradeOutStock(self, trade):

        for order in trade.inuse_orders:
            try:
                if Product.objects.isProductOutOfStock(order.outer_id,
                                                       order.outer_sku_id):
                    return True
            except Product.ProductCodeDefect:
                continue

        return False

    def isTradeFullRefund(self, trade):

        if not isinstance(trade, self.model):
            trade = self.get(id=trade)

        refund_approval_num = trade.merge_orders.filter(
            refund_status__in=pcfg.REFUND_APPROVAL_STATUS,
            gift_type=pcfg.REAL_ORDER_GIT_TYPE,
            is_merge=False) \
            .count()

        total_orders_num = trade.merge_orders.filter(
            gift_type=pcfg.REAL_ORDER_GIT_TYPE,
            is_merge=False).count()

        if refund_approval_num > 0 and refund_approval_num == total_orders_num:
            return True
        return False

    def isTradeNewRefund(self, trade):

        if not isinstance(trade, self.model):
            trade = self.get(id=trade)

        refund_orders_num = trade.merge_orders.filter(
            gift_type=pcfg.REAL_ORDER_GIT_TYPE,
            is_merge=False) \
            .exclude(refund_status__in=(pcfg.NO_REFUND,
                                        pcfg.REFUND_CLOSED,
                                        pcfg.EMPTY_STATUS)).count()

        if refund_orders_num > trade.refund_num:
            trade.refund_num = refund_orders_num
            update_model_fields(trade, update_fields=['refund_num'])
            return True

        return False

    def isTradeRefunding(self, trade):

        orders = trade.merge_orders.filter(
            refund_status=pcfg.REFUND_WAIT_SELLER_AGREE)
        if orders.count() > 0:
            return True
        return False

    def isOrderRuleMatch(self, order):
        try:
            return Product.objects.isProductRuelMatch(order.outer_id,
                                                      order.outer_sku_id)
        except Product.ProductCodeDefect:
            return False

    def isTradeRuleMatch(self, trade):

        for order in trade.inuse_orders:
            if self.isOrderRuleMatch(order):
                return True

        return False

    def isTradeMergeable(self, trade):

        if not isinstance(trade, self.model):
            trade = self.get(id=trade)

        if trade.ware_by == self.model.WARE_NONE:
            return False

        queryset = self.getMergeQueryset(trade.buyer_nick,
                                         trade.receiver_name,
                                         trade.receiver_mobile,
                                         trade.receiver_phone,
                                         state=trade.receiver_state,
                                         city=trade.receiver_city)

        order_count = queryset.count()
        if order_count == 0:
            return False

        if order_count == 1:
            return queryset[0].id != trade.id

        return True

    def diffTradeAddress(self, trade, sub_trade):

        diff_string = []
        if trade.receiver_name != sub_trade.receiver_name:
            diff_string.append('%s|%s' % (trade.receiver_name,
                                          sub_trade.receiver_name))

        if trade.receiver_mobile != sub_trade.receiver_mobile:
            diff_string.append('%s|%s' % (trade.receiver_mobile,
                                          sub_trade.receiver_mobile))

        if trade.receiver_phone != sub_trade.receiver_phone:
            diff_string.append('%s|%s' % (trade.receiver_phone,
                                          sub_trade.receiver_phone))

        if trade.receiver_state != sub_trade.receiver_state:
            diff_string.append('%s|%s' % (trade.receiver_state,
                                          sub_trade.receiver_state))

        if trade.receiver_city != sub_trade.receiver_city:
            diff_string.append('%s|%s' % (trade.receiver_city,
                                          sub_trade.receiver_city))

        if trade.receiver_district != sub_trade.receiver_district:
            diff_string.append('%s|%s' % (trade.receiver_district,
                                          sub_trade.receiver_district))

        if trade.receiver_address != sub_trade.receiver_address:
            diff_string.append('%s|%s' % (trade.receiver_address,
                                          sub_trade.receiver_address))
        return ','.join(diff_string)

    def isValidPubTime(self, userId, trade, modified):

        if not isinstance(trade, self.model):
            try:
                trade = self.get(user__visitor_id=userId, tid=trade)
            except:
                return True

        if (not trade.modified or
                    trade.modified < modified or
                not trade.sys_status):
            return True
        return False

    def updatePubTime(self, userId, trade, modified):

        if not isinstance(trade, self.model):
            trade = self.get(user__visitor_id=userId, tid=trade)

        trade.modified = modified

        update_model_fields(trade, update_fields=['modified'])

    def mapTradeFromToCode(self, trade_from):

        from .models import TF_CODE_MAP

        from_code = 0
        from_list = trade_from.split(',')
        for f in from_list:
            from_code |= TF_CODE_MAP.get(f.upper(), 0)

        return from_code

    def updateProductStockByTrade(self, trade):

        for order in trade.print_orders:

            outer_id = order.outer_id
            outer_sku_id = order.outer_sku_id
            order_num = order.num

            if outer_sku_id:
                psku = ProductSku.objects.get(product__outer_id=outer_id,
                                              outer_id=outer_sku_id)
                psku.update_quantity(order_num, dec_update=True)
                psku.update_wait_post_num(order_num, dec_update=True)

            else:
                prod = Product.objects.get(outer_id=outer_id)
                prod.update_collect_num(order_num, dec_update=True)
                prod.update_wait_post_num(order_num, dec_update=True)

                # 更新退换货商品更新商品库存
                #         for order in trade.return_orders:
                #
                #             outer_id     = order.outer_id
                #             outer_sku_id = order.outer_sku_id
                #             order_num    = order.num
                #
                #             if outer_sku_id:
                #                 psku = ProductSku.objects.get(product__outer_id=outer_id,
                #                                               outer_id=outer_sku_id)
                #                 psku.update_quantity(order_num,dec_update=False)
                #
                #             else:
                #                 prod = Product.objects.get(outer_id=outer_id)
                #                 prod.update_collect_num(order_num,dec_update=False)
                #

    def getProductOrSkuWaitPostNum(self, outer_id, outer_sku_id):
        """ 获取订单商品待发数"""
        from shopback.trades.models import MergeOrder

        wait_nums = MergeOrder.objects.filter(
            outer_id=outer_id,
            outer_sku_id=outer_sku_id,
            merge_trade__sys_status__in=pcfg.WAIT_WEIGHT_STATUS,
            sys_status=pcfg.IN_EFFECT) \
            .aggregate(sale_nums=Sum('num')).get('sale_nums')
        return wait_nums or 0

    def getProductOrSkuOrderOutingNum(self, outer_id, outer_sku_id):
        """ 获取订单商品正在出库数（包括发货准备和扫描部分的订单数量）"""
        from shopback.trades.models import MergeOrder

        outing_nums = MergeOrder.objects.filter(
            outer_id=outer_id,
            outer_sku_id=outer_sku_id,
            merge_trade__sys_status__in=
            [pcfg.WAIT_PREPARE_SEND_STATUS,
             pcfg.WAIT_CHECK_BARCODE_STATUS,
             pcfg.WAIT_SCAN_WEIGHT_STATUS],
            sys_status=pcfg.IN_EFFECT) \
            .aggregate(sale_nums=Sum('num')).get('sale_nums')
        return outing_nums or 0
