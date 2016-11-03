# -*- coding: utf-8 -*-
import datetime
from shopback.trades.mixins import TaobaoTradeService, TaobaoSendTradeMixin
from shopback.users import Seller
from shopback.orders.models import Trade, Order
from shopback.trades.models import MergeTrade, MergeOrder
from shopback.items.models import Product
from shopback.base.service import LocalService
from shopback import paramconfig as pcfg
from shopback.trades.handlers import trade_handler
from common.utils import parse_datetime, update_model_fields
from shopapp.taobao import apis


class OrderService(TaobaoSendTradeMixin, TaobaoTradeService, LocalService):
    trade = None

    def __init__(self, t):
        assert t not in ('', None)
        if isinstance(t, Trade):
            self.trade = t
        else:
            self.trade = Trade.objects.get(id=t)

    @classmethod
    def getTradeFullInfo(cls, user_id, tid, *args, **kwargs):

        update_fields = 'seller_nick,buyer_nick,title,type,' \
                        + 'created,tid,status,modified,payment,' \
                        + 'discount_fee,adjust_fee,post_fee,total_fee,' \
                        + 'point_fee,pay_time,end_time,consign_time,price,' \
                        + 'shipping_type,receiver_name,receiver_state,' \
                        + 'receiver_city,receiver_district,receiver_address,' \
                        + 'receiver_zip,receiver_mobile,receiver_phone,' \
                        + 'buyer_message,buyer_memo,seller_memo,seller_flag,' \
                        + 'send_time,is_brand_sale,is_force_wlb,trade_from,' \
                        + 'is_lgtype,lg_aging,orders,'

        response = apis.taobao_trade_fullinfo_get(
            tid=tid,
            fields=update_fields,
            tb_user_id=user_id)
        return response['trade_fullinfo_get_response']['trade']

    @classmethod
    def getTradeInfo(cls, user_id, tid, *args, **kwargs):

        update_fields = ('seller_nick,buyer_nick,title, type,created,tid,'
                         'seller_rate,buyer_rate,status,payment,discount_fee,'
                         'adjust_fee,post_fee,total_fee,pay_time,end_time,modified'
                         ',consign_time,buyer_memo,seller_memo'
                         'buyer_message,cod_fee,cod_status,shipping_type,orders')

        response = apis.taobao_trade_get(tid=tid,
                                         fields=update_fields,
                                         tb_user_id=user_id)
        return response['trade_get_response']['trade']

    @classmethod
    def saveOrderByDict(cls, trade, order_dict, *args, **kwargs):

        order, state = Order.objects.get_or_create(pk=order_dict['oid'])
        order.trade = trade

        for k, v in order_dict.iteritems():
            if k.endswith('fee') or k.endswith('payment'):
                v = float(v or 0.0)
            hasattr(order, k) and setattr(order, k, v)

        divide_order_fee = order_dict.get('divide_order_fee', None)
        if divide_order_fee:
            order.payment = float(divide_order_fee)

        order.outer_id = order_dict.get('outer_iid', '')
        order.save()

        return order

    @classmethod
    def saveTradeByDict(cls, user_id, trade_dict, *args, **kwargs):

        if not trade_dict.get('tid'):
            return

        trade, state = Trade.objects.get_or_create(pk=trade_dict['tid'],
                                                   seller_id=user_id)
        trade.user = Seller.getOrCreateSeller(user_id)
        trade.seller_id = user_id

        for k, v in trade_dict.iteritems():
            if k.endswith('fee') or k.endswith('payment'):
                v = float(v or 0.0)
            hasattr(trade, k) and setattr(trade, k, v)

        trade.save()

        for o in trade_dict['orders']['order']:
            cls.saveOrderByDict(trade, o)

        return trade

    @classmethod
    def createTrade(cls, user_id, tid, *args, **kwargs):

        trade_dict = cls.getTradeInfo(user_id, tid)

        return cls.saveTradeByDict(user_id, trade_dict)

    @classmethod
    def createMergeOrder(cls, merge_trade, order, *args, **kwargs):

        merge_order, state = MergeOrder.objects.get_or_create(oid=order.oid,
                                                              merge_trade=merge_trade)
        state = state or not merge_order.sys_status

        if (order.status in (pcfg.TRADE_CLOSED,
                             pcfg.TRADE_CLOSED_BY_TAOBAO)):
            sys_status = pcfg.INVALID_STATUS
        else:
            sys_status = merge_order.sys_status or pcfg.IN_EFFECT

        if state:
            order_fields = ['num_iid', 'title', 'price', 'sku_id', 'num', 'outer_id'
                , 'outer_sku_id', 'total_fee', 'payment', 'refund_status'
                , 'pic_path', 'seller_nick', 'buyer_nick', 'created'
                , 'pay_time', 'consign_time', 'status']

            for k in order_fields:
                setattr(merge_order, k, getattr(order, k))

            code_tuple = Product.objects.trancecode(order.outer_id,
                                                    order.outer_sku_id)

            merge_order.outer_id = code_tuple[0]
            merge_order.outer_sku_id = code_tuple[1]
            merge_order.created = merge_trade.created
            merge_order.pay_time = merge_trade.pay_time
            merge_order.sku_properties_name = order.properties_values
            merge_order.sys_status = sys_status
        else:
            merge_order.refund_status = order.refund_status
            merge_order.created = merge_trade.created
            merge_order.pay_time = merge_trade.pay_time
            merge_order.consign_time = merge_trade.consign_time
            merge_order.status = order.status
            merge_order.sys_status = sys_status
        merge_order.save()

        return merge_order

    @classmethod
    def createMergeTrade(cls, trade, *args, **kwargs):

        tid = trade.id
        update_address = False
        merge_trade, state = MergeTrade.objects.get_or_create(user=trade.user,
                                                              tid=tid,
                                                              type=pcfg.TAOBAO_TYPE)

        update_fields = ['buyer_nick', 'is_force_wlb'
            , 'seller_cod_fee', 'buyer_cod_fee', 'cod_fee', 'cod_status'
            , 'seller_flag', 'created', 'pay_time', 'modified', 'consign_time'
            , 'send_time', 'status', 'is_brand_sale', 'is_lgtype', 'lg_aging'
            , 'lg_aging_type', 'buyer_rate', 'seller_rate', 'seller_can_rate'
            , 'is_part_consign', 'step_paid_fee', 'step_trade_status']

        if not merge_trade.receiver_name and trade.receiver_name:
            update_address = True
            address_fields = ['receiver_name', 'receiver_state',
                              'receiver_city', 'receiver_district',
                              'receiver_address', 'receiver_zip',
                              'receiver_mobile', 'receiver_phone']

            update_fields.extend(address_fields)

        for k in update_fields:
            setattr(merge_trade, k, getattr(trade, k))

        merge_trade.is_cod = trade.type == pcfg.COD_TYPE
        merge_trade.payment = merge_trade.payment or trade.payment
        merge_trade.total_fee = merge_trade.total_fee or trade.total_fee
        merge_trade.discount_fee = merge_trade.discount_fee or trade.discount_fee
        merge_trade.adjust_fee = merge_trade.adjust_fee or trade.adjust_fee
        merge_trade.post_fee = merge_trade.post_fee or trade.post_fee

        merge_trade.trade_from = MergeTrade.objects.mapTradeFromToCode(trade.trade_from)
        merge_trade.shipping_type = (merge_trade.shipping_type or
                                     pcfg.SHIPPING_TYPE_MAP.get(trade.shipping_type,
                                                                pcfg.EXPRESS_SHIPPING_TYPE))

        update_model_fields(merge_trade, update_fields=update_fields
                                                       + ['is_cod', 'shipping_type', 'payment', 'total_fee',
                                                          'discount_fee', 'adjust_fee', 'post_fee', 'trade_from'])

        for order in trade.trade_orders.all():
            cls.createMergeOrder(merge_trade, order)

        trade_handler.proccess(
            merge_trade,
            **{'origin_trade': trade,
               'update_address': (update_address and
                                  merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS),
               'first_pay_load': (merge_trade.sys_status == pcfg.EMPTY_STATUS
                                  and merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS)})

        return merge_trade

    def payTrade(self, *args, **kwargs):

        trade_dict = self.getTradeFullInfo(self.get_seller_id(), self.get_trade_id())
        trade = self.saveTradeByDict(self.get_seller_id(), trade_dict)

        return self.createMergeTrade(trade)

    def ShipTrade(self, oid, *args, **kwargs):

        self.trade.trade_orders.filter(oid=oid) \
            .update(status=pcfg.WAIT_BUYER_CONFIRM_GOODS)

        self.trade.status = pcfg.WAIT_BUYER_CONFIRM_GOODS
        self.trade.consign_time = datetime.datetime.now()
        self.trade.save()

    def finishTrade(self, finish_time, *args, **kwargs):

        pass

    def memoTrade(self, *args, **kwargs):
        pass

    def closeTrade(self, *args, **kwargs):
        pass

    def changeTrade(self, *args, **kwargs):
        pass

    def changeTradeOrder(self, oid, *args, **kwargs):
        pass

    def remindTrade(self, *args, **kwargs):
        pass
