# -*- coding:utf8 -*-
import json
import datetime
from collections import defaultdict

from common.modelutils import update_model_fields, update_model_change_fields
from .models import SaleTrade, SaleOrder, SaleRefund, District, FLASH_SELLER_ID
from shopback.base.service import LocalService
from shopback import paramconfig as pcfg
from shopapp.weixin.models import MIAOSHA_SELLER_ID
from shopback.users.models import User

import logging
logger = logging.getLogger(__name__)


def recursive_append_child_districts(node, node_maps):
    copy_node = node.copy()
    child_nodes = node_maps.get(copy_node['id'])
    if not child_nodes:
        return copy_node

    copy_node.setdefault('childs', [])
    for child_node in child_nodes:
        child_node = recursive_append_child_districts(child_node, node_maps)
        copy_node['childs'].append(child_node)
    return copy_node

def get_district_json_data():
    districts = District.objects.filter(is_valid=True).order_by('parent_id', 'sort_order')
    districts_values = districts.values('id', 'parent_id', 'name', 'zipcode', 'grade')

    districts_tree_nodes = defaultdict(list)
    for district in districts_values:
        districts_tree_nodes[district['parent_id']].append(district)

    node_tree = recursive_append_child_districts({'id':0 }, districts_tree_nodes)
    return node_tree.get('childs', [])


class FlashSaleService(LocalService):
    trade = None

    def __init__(self, t):

        assert t not in ('', None)
        if isinstance(t, SaleTrade):
            self.trade = t
        else:
            self.trade = SaleTrade.objects.get(tid=t)

    @classmethod
    def createMergeOrder(cls, merge_trade, order, *args, **kwargs):

        from shopback.trades.models import MergeOrder
        from shopback.items.models import Product, ProductSku

        order_id = order.oid
        merge_order, state = MergeOrder.objects.get_or_create(oid=order_id,
                                                              merge_trade=merge_trade)
        state = state or not merge_order.sys_status
        update_prams = {}
        if state and (order.status in (SaleOrder.TRADE_CLOSED,
                                       SaleOrder.TRADE_CLOSED_BY_SYS) or
                              order.refund_status in SaleRefund.REFUNDABLE_STATUS or
                              merge_trade.status in (pcfg.TRADE_CLOSED, SaleTrade.TRADE_CLOSED_BY_SYS)):
            sys_status = pcfg.INVALID_STATUS
        else:
            sys_status = merge_order.sys_status or pcfg.IN_EFFECT

        if state:
            product = Product.objects.get(id=order.item_id)
            sku = ProductSku.objects.get(id=order.sku_id, product=product)

            update_prams['payment'] = order.payment
            update_prams['total_fee'] = order.total_fee

            update_prams['num'] = order.num
            update_prams['title'] = order.title
            update_prams['outer_id'] = product.outer_id
            update_prams['sku_properties_name'] = order.sku_name
            update_prams['outer_sku_id'] = sku.outer_id
            update_prams['sku_id']  = sku.id
            update_prams['num_iid'] = product.id

        update_prams['created'] = merge_trade.created
        update_prams['pay_time'] = merge_trade.pay_time
        update_prams['status'] = merge_trade.status
        update_prams['sys_status'] = sys_status
        update_prams['refund_fee'] = order.refund_fee
        update_prams['refund_status'] = dict(SaleRefund.REFUND_STATUS_MAP).get(order.refund_status)

        update_model_change_fields(merge_order, update_params=update_prams, trigger_signals=True)
        return merge_order

    @classmethod
    def getOrCreateSeller(cls, trade):

        seller_id = FLASH_SELLER_ID
        seller_type = User.SHOP_TYPE_SALE
        for order in trade.normal_orders:
            if order.title.find(u'秒杀') >= 0:
                ###取消秒杀单独分配一个店铺, meron.2015-10-28
                #                 seller_id   = MIAOSHA_SELLER_ID
                #                 seller_type = User.SHOP_TYPE_WX
                if trade.buyer_nick.find(u'[秒杀]') < 0:
                    trade.buyer_nick = u'[秒杀]' + trade.buyer_nick
                break
        seller = User.getOrCreateSeller(seller_id, seller_type=seller_type)
        return seller

    @classmethod
    def createMergeTrade(cls, trade, *args, **kwargs):
        return
        from shopback.trades.handlers import trade_handler
        from shopback.trades.models import MergeTrade

        seller = cls.getOrCreateSeller(trade)
        merge_trade, state = MergeTrade.objects.get_or_create(tid=trade.tid,
                                                              user=seller)

        update_fields = ['buyer_nick', 'created', 'pay_time', 'modified', 'status', 'buyer_message']

        merge_trade.buyer_nick = trade.buyer_nick.strip() or trade.receiver_mobile

        merge_trade.buyer_message = trade.buyer_message

        merge_trade.created = trade.created
        merge_trade.modified = trade.modified
        merge_trade.pay_time = trade.pay_time
        merge_trade.status = SaleTrade.mapTradeStatus(trade.status)

        update_address = False
        if not merge_trade.receiver_name and trade.receiver_name:
            update_address = True
            address_fields = ['receiver_name', 'receiver_state',
                              'receiver_city', 'receiver_address',
                              'receiver_district', 'receiver_mobile',
                              'receiver_phone']

            for k in address_fields:
                setattr(merge_trade, k, getattr(trade, k))

            update_fields.extend(address_fields)

        merge_trade.payment = merge_trade.payment or float(trade.payment)
        merge_trade.total_fee = merge_trade.total_fee or float(trade.total_fee)
        merge_trade.post_fee = merge_trade.post_fee or float(trade.post_fee)

        merge_trade.trade_from = 0
        merge_trade.shipping_type = pcfg.EXPRESS_SHIPPING_TYPE
        merge_trade.type = pcfg.SALE_TYPE

        update_model_fields(merge_trade, update_fields=update_fields
                                                       + ['shipping_type', 'type', 'payment',
                                                          'total_fee', 'post_fee', 'trade_from'])

        for order in trade.sale_orders.all():
            cls.createMergeOrder(merge_trade, order)

        trade_handler.proccess(merge_trade,
                               **{'origin_trade': trade,
                                  'update_address': (update_address and
                                                     merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS),
                                  'first_pay_load': (
                                      merge_trade.sys_status == pcfg.EMPTY_STATUS and
                                      merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS)})

        return merge_trade

    def payTrade(self, *args, **kwargs):
        from shopback.items.models import ProductSku
        ########################## 押金链接，不需仓库处理 ######################
        outer_ids = set([o[0] for o in self.trade.normal_orders.values_list('outer_id')])
        if len(outer_ids) == 1 and list(outer_ids)[0].startswith('RMB'):
            return
        if self.trade.order_type == SaleTrade.SALE_ORDER:
            return
            ###################################################################
        self.__class__.createMergeTrade(self.trade)
        # for sale_order in self.trade.sale_orders.all():
        #    ProductSku.objects.get(id=sale_order.sku_id).assign_packages()
        return

    def sendTrade(self, company_code=None, out_sid=None, merge_trade=None, retry_times=3, *args, **kwargs):
        from shopback.logistics.models import LogisticsCompany
        consign_time = datetime.datetime.now()
        buyer_id = self.trade.buyer_id
        try:
            for morder in merge_trade.normal_orders:  #
                sorders = SaleOrder.objects.filter(oid=morder.oid,
                                                   sale_trade__buyer_id=buyer_id)
                if not sorders.exists() or sorders[0].status != SaleOrder.WAIT_SELLER_SEND_GOODS:
                    continue
                sorder = sorders[0]
                sorder.consign_time = consign_time
                sorder.status = SaleOrder.WAIT_BUYER_CONFIRM_GOODS
                sorder.save()

            if not company_code:
                lg = LogisticsCompany.getNoPostCompany()
            else:
                lg = LogisticsCompany.objects.get(code=company_code)
            self.trade.logistics_company = lg
            self.trade.out_sid = out_sid
            wait_confirm_orders = self.trade.sale_orders.filter(status=SaleOrder.WAIT_BUYER_CONFIRM_GOODS)
            wait_send_orders = self.trade.sale_orders.filter(status=SaleOrder.WAIT_SELLER_SEND_GOODS)
            if wait_confirm_orders.count() > 0 and wait_send_orders.count() == 0:
                self.trade.consign_time = consign_time
                self.trade.status = SaleTrade.WAIT_BUYER_CONFIRM_GOODS
            self.trade.save()
        except Exception, exc:
            logger.error(exc.message, exc_info=True)


