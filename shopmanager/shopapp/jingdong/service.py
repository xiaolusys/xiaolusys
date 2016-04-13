# -*- coding:utf8 -*-
import json
from .models import JDShop, JDOrder, JDProduct, JDLogistic
from shopback.base.service import LocalService
from shopback import paramconfig as pcfg
from common.utils import update_model_fields
from .apis import api


class JDShopService(LocalService):
    trade = None

    def __init__(self, t):

        assert t not in ('', None)
        if isinstance(t, JDOrder):
            self.trade = t
        else:
            self.trade = JDOrder.objects.get(order_id=t)

    @classmethod
    def createTradeByDict(cls, user_id, trade_dict, *args, **kwargs):

        jd_shop = JDShop.objects.get(vender_id=trade_dict['vender_id'])
        jd_order, state = JDOrder.objects.get_or_create(order_id=trade_dict['order_id'],
                                                        shop=jd_shop)

        for k, v in trade_dict.iteritems():
            if v and k in ('consignee_info', 'item_info_list', 'coupon_detail_list'):
                v = json.dumps(v)
            if k in ('order_start_time', 'order_end_time', 'modified', 'payment_confirm_time'):
                v = v or None
            hasattr(jd_order, k) and setattr(jd_order, k, v)

        jd_order.save()

        return jd_order

    @classmethod
    def createTrade(cls, user_id, tid, *args, **kwargs):

        response = api.jd_order_get(order_id=tid, jd_user_id=user_id)
        order_dict = response['orderInfo']

        return cls.createTradeByDict(user_id, order_dict)

    @classmethod
    def createMergeOrder(cls, merge_trade, order, *args, **kwargs):

        from shopback.trades.models import MergeOrder
        from shopback.items.models import Product

        order_id = 'j%s%s' % (merge_trade.tid, order['sku_id'])
        merge_order, state = MergeOrder.objects.get_or_create(oid=order_id,
                                                              merge_trade=merge_trade)
        state = state or not merge_order.sys_status

        if (merge_trade.status == pcfg.TRADE_CLOSED):
            sys_status = pcfg.INVALID_STATUS
        else:
            sys_status = merge_order.sys_status or pcfg.IN_EFFECT

        if state:
            outer_id, outer_sku_id = Product.objects.trancecode(order['outer_sku_id'], '')

            merge_order.payment = round((merge_trade.payment / merge_trade.total_fee)
                                        * float(order['jd_price']), 2)
            merge_order.total_fee = order['jd_price']

            merge_order.num = order['item_total']
            merge_order.title = order['sku_name']
            merge_order.outer_id = outer_id
            merge_order.outer_sku_id = outer_sku_id

        merge_order.created = merge_trade.created
        merge_order.pay_time = merge_trade.pay_time
        merge_order.status = merge_trade.status
        merge_order.sys_status = sys_status
        merge_order.save()

        return merge_order

    @classmethod
    def createMergeTrade(cls, trade, *args, **kwargs):

        from shopback.trades.handlers import trade_handler
        from shopback.trades.models import MergeTrade
        from shopback.users.models import User

        seller = User.getOrCreateSeller(trade.shop.vender_id, seller_type=User.SHOP_TYPE_JD)
        merge_trade, state = MergeTrade.objects.get_or_create(tid=trade.order_id,
                                                              user=seller)

        update_fields = ['buyer_nick', 'created', 'pay_time', 'modified', 'status']

        merge_trade.buyer_nick = trade.pin

        merge_trade.created = trade.order_start_time
        merge_trade.modified = trade.modified
        merge_trade.pay_time = trade.payment_confirm_time
        merge_trade.status = JDOrder.mapTradeStatus(trade.order_state)

        update_address = False
        if not merge_trade.receiver_name and trade.consignee_info:
            update_address = True
            receiver_info = json.loads(trade.consignee_info)
            merge_trade.receiver_name = receiver_info['fullname']
            merge_trade.receiver_state = receiver_info['province']
            merge_trade.receiver_city = receiver_info['city']
            merge_trade.receiver_district = receiver_info['county']
            merge_trade.receiver_address = receiver_info['full_address']
            merge_trade.receiver_mobile = receiver_info['mobile']
            merge_trade.receiver_phone = receiver_info['telephone']

            address_fields = ['receiver_name', 'receiver_state',
                              'receiver_city', 'receiver_address',
                              'receiver_district', 'receiver_mobile',
                              'receiver_phone']

            update_fields.extend(address_fields)

        merge_trade.payment = merge_trade.payment or float(trade.order_payment)
        merge_trade.total_fee = merge_trade.total_fee or float(trade.order_total_price)
        merge_trade.post_fee = merge_trade.post_fee or float(trade.freight_price)

        merge_trade.trade_from = 0
        merge_trade.shipping_type = pcfg.EXPRESS_SHIPPING_TYPE
        merge_trade.type = pcfg.JD_TYPE

        update_model_fields(merge_trade, update_fields=update_fields
                                                       + ['shipping_type', 'type', 'payment',
                                                          'total_fee', 'post_fee', 'trade_from'])

        if trade.item_info_list:
            item_list = json.loads(trade.item_info_list)
            for item in item_list:
                cls.createMergeOrder(merge_trade, item)

        trade_handler.proccess(merge_trade,
                               **{'origin_trade': trade,
                                  'update_address': (update_address and
                                                     merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS),
                                  'first_pay_load': (
                                      merge_trade.sys_status == pcfg.EMPTY_STATUS and
                                      merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS)})

        return merge_trade

    def payTrade(self, *args, **kwargs):

        trade = self.__class__.createTrade(self.trade.shop.vender_id,
                                           self.trade.order_id)

        return self.__class__.createMergeTrade(trade)

    def sendTrade(self, company_code=None, out_sid=None, retry_times=3, *args, **kwargs):

        try:
            jd_logistic = JDLogistic.objects.get(company_code__icontains
                                                 =company_code.split('_')[0])

            response = api.jd_order_sop_outstorage(order_id=self.trade.order_id,
                                                   logistics_id=jd_logistic.logistics_id,
                                                   waybill=out_sid,
                                                   trade_no=kwargs.get('serial_no', None),
                                                   jd_user_id=self.trade.shop.vender_id)
        except Exception, exc:
            raise exc
