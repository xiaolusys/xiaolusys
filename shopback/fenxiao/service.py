# -*- coding: utf-8 -*-
import json
import datetime
from shopback.users.models import User as Seller
from shopback.base.service import LocalService
from shopback.trades.mixins import TaobaoTradeService, TaobaoSendTradeMixin
from shopback.trades.models import MergeTrade, MergeOrder
from shopback.logistics.models import Logistics
from shopback.items.models import Product
from shopback.fenxiao.models import FenxiaoProduct, PurchaseOrder, SubPurchaseOrder
from shopback.trades.handlers import trade_handler
from shopback import paramconfig as pcfg
from common.utils import update_model_fields
from shopapp.taobao import apis


class PurchaseOrderService(TaobaoSendTradeMixin, TaobaoTradeService, LocalService):
    trade = None

    def __init__(self, t):
        assert t not in ('', None)

        if isinstance(t, PurchaseOrder):
            self.trade = t
        else:
            self.trade = PurchaseOrder.objects.get(id=t)

    @classmethod
    def getPurchaseOrderInfo(cls, user_id, fenxiao_id, *args, **kwargs):

        response = apis.taobao_fenxiao_orders_get(purchase_order_id=fenxiao_id,
                                                  tb_user_id=user_id)
        return response['fenxiao_orders_get_response']['purchase_orders']['purchase_order'][0]

    @classmethod
    def saveSubPurchaseOrderByDict(cls, purchase_order, order_dict, *args, **kwargs):

        sub_purchase_order, state = SubPurchaseOrder.objects. \
            get_or_create(fenxiao_id=order_dict['fenxiao_id'])

        for k, v in order_dict.iteritems():
            if k.endswith('fee') or k.endswith('payment'):
                v = float(v or 0.0)
            hasattr(sub_purchase_order, k) and setattr(sub_purchase_order, k, v)

        sub_purchase_order.purchase_order = purchase_order
        sub_purchase_order.fenxiao_product = FenxiaoProduct.get_or_create(
            purchase_order.seller_id, order_dict['item_id'])

        sub_purchase_order.save()

        return sub_purchase_order

    @classmethod
    def savePurchaseOrderByDict(cls, user_id, trade_dict, *args, **kwargs):

        purchase_order, state = PurchaseOrder.objects. \
            get_or_create(fenxiao_id=trade_dict['fenxiao_id'])
        purchase_order.user = Seller.objects.get(visitor_id=user_id)
        purchase_order.seller_id = user_id
        sub_purchase_orders = trade_dict.pop('sub_purchase_orders')

        for k, v in trade_dict.iteritems():
            if k.endswith('fee') or k.endswith('payment') or k.endswith('price'):
                v = float(v or 0.0)
            hasattr(purchase_order, k) and setattr(purchase_order, k, v)

        purchase_order.save()

        for sub_order in sub_purchase_orders['sub_purchase_order']:
            cls.saveSubPurchaseOrderByDict(purchase_order, sub_order)

        return purchase_order

    @classmethod
    def createTrade(cls, user_id, tid, *args, **kwargs):

        trade_dict = cls.getPurchaseOrderInfo(user_id, tid)

        return cls.savePurchaseOrderByDict(user_id, trade_dict)

    @classmethod
    def createMergeOrder(cls, merge_trade, order, *args, **kwargs):

        merge_order, state = MergeOrder.objects.get_or_create(oid=order.fenxiao_id,
                                                              merge_trade=merge_trade)
        state = state or not merge_order.sys_status
        fenxiao_product = FenxiaoProduct.get_or_create(merge_trade.user.visitor_id,
                                                       order.item_id)

        if order.status == pcfg.TRADE_REFUNDING:
            refund_status = pcfg.REFUND_WAIT_SELLER_AGREE
        elif order.status == pcfg.TRADE_REFUNDED:
            refund_status = pcfg.REFUND_SUCCESS
        else:
            refund_status = pcfg.NO_REFUND
        if (merge_order.refund_status != refund_status
            and order.status in (pcfg.TRADE_REFUNDING,
                                 pcfg.TRADE_CLOSED,
                                 pcfg.TRADE_REFUNDED)):
            sys_status = pcfg.INVALID_STATUS
        else:
            sys_status = merge_order.sys_status or pcfg.IN_EFFECT

        if state:
            merge_order.num_iid = fenxiao_product.item_id
            merge_order.title = order.title
            merge_order.price = order.price
            merge_order.sku_id = order.sku_id
            merge_order.num = order.num

            code_tuple = Product.objects.trancecode(order.item_outer_id,
                                                    order.sku_outer_id)
            merge_order.outer_id = code_tuple[0]
            merge_order.outer_sku_id = code_tuple[1]

            merge_order.total_fee = order.total_fee
            merge_order.payment = order.distributor_payment
            merge_order.sku_properties_name = order.properties_values
            merge_order.refund_status = refund_status
            merge_order.pic_path = fenxiao_product.pictures and fenxiao_product.pictures.split(',')[0] or ''
            merge_order.seller_nick = merge_trade.user.nick
            merge_order.buyer_nick = merge_trade.buyer_nick
            merge_order.created = order.created
            merge_order.pay_time = merge_trade.created
            merge_order.consign_time = merge_trade.consign_time
            merge_order.status = pcfg.FENXIAO_TAOBAO_STATUS_MAP.get(order.status, order.status)
            merge_order.sys_status = sys_status
        else:
            merge_order.refund_status = refund_status
            merge_order.payment = order.distributor_payment
            merge_order.created = order.created
            merge_order.pay_time = merge_trade.created
            merge_order.consign_time = merge_trade.consign_time
            merge_order.status = order.status
            merge_order.sys_status = sys_status
        merge_order.save()

        return merge_order

    @classmethod
    def createMergeTrade(cls, trade, *args, **kwargs):

        tid = trade.id
        merge_trade, state = MergeTrade.objects.get_or_create(user=trade.user,
                                                              tid=tid,
                                                              type=pcfg.FENXIAO_TYPE)

        update_fields = ['buyer_nick', 'payment', 'shipping_type', 'total_fee'
            , 'post_fee', 'created', 'trade_from', 'pay_time', 'modified'
            , 'consign_time', 'seller_flag', 'priority', 'status']

        if not merge_trade.receiver_name and \
                        trade.status not in ('',
                                             pcfg.TRADE_NO_CREATE_PAY,
                                             pcfg.WAIT_BUYER_PAY,
                                             pcfg.TRADE_CLOSED,
                                             pcfg.TRADE_CLOSED_BY_TAOBAO):
            logistics = Logistics.get_or_create(trade.user.visitor_id, tid)
            location = json.loads(logistics.location or 'null')

            merge_trade.receiver_name = logistics.receiver_name
            merge_trade.receiver_zip = location.get('zip', '') if location else ''
            merge_trade.receiver_mobile = logistics.receiver_mobile
            merge_trade.receiver_phone = logistics.receiver_phone

            merge_trade.receiver_state = location.get('state', '') if location else ''
            merge_trade.receiver_city = location.get('city', '') if location else ''
            merge_trade.receiver_district = location.get('district', '') if location else ''
            merge_trade.receiver_address = location.get('address', '') if location else ''

            address_fields = ['receiver_name', 'receiver_state',
                              'receiver_city', 'receiver_district',
                              'receiver_address', 'receiver_zip',
                              'receiver_mobile', 'receiver_phone']

            update_fields.extend(address_fields)

        merge_trade.payment = merge_trade.payment or trade.distributor_payment
        merge_trade.total_fee = merge_trade.total_fee or trade.total_fee
        merge_trade.post_fee = merge_trade.post_fee or trade.post_fee

        merge_trade.buyer_nick = trade.distributor_username
        merge_trade.shipping_type = merge_trade.shipping_type or \
                                    pcfg.SHIPPING_TYPE_MAP.get(trade.shipping, pcfg.EXPRESS_SHIPPING_TYPE)
        merge_trade.created = trade.created
        merge_trade.pay_time = trade.created
        merge_trade.modified = trade.modified
        merge_trade.consign_time = trade.consign_time
        merge_trade.seller_flag = trade.supplier_flag
        merge_trade.priority = 0
        merge_trade.status = trade.status
        merge_trade.trade_from = MergeTrade.objects.mapTradeFromToCode(pcfg.TF_TAOBAO)

        update_model_fields(merge_trade, update_fields=update_fields)

        # 保存分销订单到抽象全局抽象订单表
        for order in trade.sub_purchase_orders.all():
            cls.createMergeOrder(merge_trade, order)

        trade_handler.proccess(merge_trade,
                               **{'origin_trade': trade,
                                  'first_pay_load': (
                                      merge_trade.sys_status == pcfg.EMPTY_STATUS
                                      and merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS)})

        return merge_trade

    def payTrade(self, *args, **kwargs):
        if self.get_trade_id():
            return MergeTrade.objects.get(tid=self.get_trade_id())

    def ShipTrade(self, oid, *args, **kwargs):

        self.trade.sub_purchase_orders.filter(fenxiao_id=oid) \
            .update(status=pcfg.WAIT_BUYER_CONFIRM_GOODS)

        self.trade.status = pcfg.WAIT_BUYER_CONFIRM_GOODS
        self.trade.consign_time = datetime.datetime.now()
        self.trade.save()

    def finishTrade(self, *args, **kwargs):
        pass

    def closeTrade(self, *args, **kwargs):
        pass

    def modifyTrade(self, *args, **kwargs):
        pass

    def changeTradeOrder(self, oid, *args, **kwargs):
        pass

    def remindTrade(self, *args, **kwargs):
        pass
