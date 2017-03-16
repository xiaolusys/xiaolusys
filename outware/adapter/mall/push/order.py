# coding: utf8
from __future__ import absolute_import, unicode_literals

from shopback.items.models import ProductSku
from supplychain.supplier.models import SaleSupplier
from outware.adapter.ware.pull import oms, pms
from outware.fengchao.models import FengchaoOrderChannel
from flashsale.pay.models import UserAddress, SaleOrder
from outware.models.oms import OutwarePackageSku

from core.apis import DictObject
from .... import constants


def push_outware_order_by_sale_trade(sale_trade):
    """ 创建订单 """
    fc_order_channel = FengchaoOrderChannel.get_default_channel()
    if not fc_order_channel:
        raise Exception('需要添加蜂巢订单来源渠道')

    order_code = sale_trade.tid
    store_code = '' # TODO#MERON 暂不指定仓库, 后面需要再变更
    address = sale_trade.get_useraddress_instance()
    params = {
        # 'store_code': warehouse.store_code,
        'order_number': sale_trade.tid,
        'order_create_time': sale_trade.created.strftime('%Y-%m-%d %H:%M:%S'),
        'pay_time': sale_trade.pay_time.strftime('%Y-%m-%d %H:%M:%S'),
        'order_type': constants.ORDER_TYPE_USUAL['code'], # TODO@MERON　是否考虑预售
        'channel_id': fc_order_channel.channel_id,
        'receiver_info': {
            'receiver_province': address.receiver_state,
            'receiver_city': address.receiver_city,
            'receiver_area': address.receiver_district,
            'receiver_address': address.receiver_address,
            'receiver_name': address.receiver_name,
            'receiver_mobile': address.receiver_mobile,
            'receiver_phone': address.receiver_phone,
        },
        'order_items': [],
        'object': 'OutwareOrder',
    }
    normal_orders = sale_trade.normal_orders
    for order in normal_orders:
        params['order_items'].append({
            'sku_order_code':order.oid,
            'sku_id': order.outer_sku_id,
            'quantity': order.num,
            'object': 'OutwareOrderSku',
        })

    dict_obj = DictObject().fresh_form_data(params)
    response = oms.create_order(order_code, store_code, dict_obj)

    return response


def push_outware_inbound_by_sale_refund(sale_refund):
    """ 创建销退单,　现只支持一个退货单创建一个销退入仓单 """

    warehouse = sale_refund.get_warehouse_object()
    sale_order = SaleOrder.objects.get(id=sale_refund.order_id)

    fc_order_channel = FengchaoOrderChannel.get_default_channel()
    ow_packagesku = OutwarePackageSku.objects.filter(origin_skuorder_no=sale_order).first()
    if not ow_packagesku:
        raise Exception('用户订单包裹信息未找到:order_id=%s'%sale_refund.order_id)

    sale_supplier = SaleSupplier.objects.get(batch_no=ow_packagesku.batch_no).only('id','vendor_code')
    params = {
        'store_code': warehouse.store_code,
        'order_code': sale_refund.refund_no,
        'vendor_code': sale_supplier.vendor_code,
        'channel_id': fc_order_channel.channel_id,
        'order_type': constants.ORDER_REFUND['code'],
        'prev_order_code': ow_packagesku.package.package_order_code,
        'receiver_info': {
            'receiver_province': warehouse.province,
            'receiver_city': warehouse.city,
            'receiver_area': warehouse.district,
            'receiver_address': warehouse.address,
            'receiver_name': warehouse.manager,
            'receiver_mobile': warehouse.mobile,
            'receiver_phone': warehouse.phone,
            'object': 'UserAddress',
        },
        'order_items': [{
            'sku_id': sale_order.outer_sku_id,
            'sku_name': sale_order.title + sale_order.sku_name,
            'quantity': sale_refund.refund_num,
            'batch_no': ow_packagesku.batch_no,
            'object': 'OutwareInboundSku',
        }],
        'object': 'OutwareInboundOrder',
    }

    dict_obj = DictObject().fresh_form_data(params)
    response = pms.create_inbound_order(dict_obj.order_code, dict_obj.vendor_code, dict_obj)

    return response

