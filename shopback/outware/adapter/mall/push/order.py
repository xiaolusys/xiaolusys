# coding: utf8
from __future__ import absolute_import, unicode_literals

from shopback.items.models import ProductSku
from pms.supplier.models import SaleSupplier, SaleProduct
from shopback.outware.adapter.ware.pull import oms, pms
from flashsale.pay.models import UserAddress, SaleOrder
from ....models import OutwarePackageSku, OutwareOrderSku, OutwareSku
from shopback.outware.fengchao import sdks
from shopback.outware.adapter.mall.push import base
from core.apis import DictObject
from .... import constants


def push_outware_order_by_package(package):
    """
        创建包裹
    """
    order_code = package.pid
    store_code = ''
    address = package.user_address
    sku_codes = []
    order_items = []
    package_skus = package.package_sku_items
    source_type_set = set()
    for psi in package_skus.iterator():
        order_items.append({
            'sku_order_code': psi.oid,
            'sku_id': psi.outer_sku_id,
            'quantity': psi.num,
            'object': 'OutwareOrderSku',
        })
        sku_codes.append(psi.outer_sku_id)
        # TODO@2017.4.19 未考虑多供应商供货情况
        product_sku = ProductSku.objects.get(id=psi.sku_id)
        model_product = product_sku.product.product_model
        source_type_set.add(model_product.source_type)

    vendor_codes = OutwareSku.objects.filter(sku_code__in=sku_codes)\
        .values_list('outware_supplier__vendor_code', flat=True)
    channel_maps = sdks.get_channelid_by_vendor_codes(vendor_codes)
    if not channel_maps or len(set(channel_maps.values())) > 1:
        raise Exception('同一订单只能有且只有一个channelid属性:packageorder=%s'%order_code)

    if not source_type_set or len(source_type_set) > 1:
        raise Exception('商品对应货源来源类型不唯一：package: %s, source_types: [%s]'%(package.pid, ','.join(source_type_set)))

    order_type = constants.ORDER_TYPE_USUAL['code']
    if list(source_type_set)[0] == SaleProduct.SOURCE_BONDED:
        order_type = constants.ORDER_TYPE_CROSSBOADER['code']

    if list(source_type_set)[0] == SaleProduct.SOURCE_OUTSIDE:
        raise Exception('直邮模式暂不支持')

    params = {
        'order_number': '{}'.format(package.pid),
        'order_create_time': package_skus.order_by('pay_time').first().created.strftime('%Y-%m-%d %H:%M:%S'),
        'pay_time': package_skus.order_by('-pay_time').first().created.strftime('%Y-%m-%d %H:%M:%S'),
        # 'order_type': order_type, # TODO@MERON　跨境订单不需要此字段，默认不接口内条件补填
        'channel_id': channel_maps.values()[0],
        'receiver_info': {
            'receiver_country': '中国',
            'receiver_province': address.receiver_state,
            'receiver_city': address.receiver_city,
            'receiver_area': address.receiver_district,
            'receiver_address': address.receiver_address,
            'receiver_name': address.receiver_name,
            'receiver_mobile': address.receiver_mobile,
            'receiver_phone': address.receiver_phone,
            'object': 'OutwareAddress',
        },
        'order_items': order_items,
        'object': 'OutwareOrder',
    }
    # TODO@MERON, 2017.4.19 ,跨境订单默认只支持保税报关方式
    if order_type == constants.ORDER_TYPE_CROSSBOADER['code']:
        params['declare_type'] = constants.DECLARE_TYPE_BOUND['code']
        params['order_person_idname'] = address.receiver_name
        params['order_person_idcard'] = address.idcard_no
        # params['receiver_info']['receiver_identity']   = address.idcard_no

    dict_obj = DictObject().fresh_form_data(params)
    response = oms.create_order(order_code, store_code, order_type, dict_obj)

    return response


def push_outware_order_by_sale_trade(sale_trade):
    """ 创建订单 """
    # fc_order_channel = FengchaoOrderChannel.get_default_channel()
    # if not fc_order_channel:
    #     raise Exception('需要添加蜂巢订单来源渠道')

    order_code = sale_trade.tid
    store_code = '' # TODO#MERON 暂不指定仓库, 后面需要再变更
    address = sale_trade.get_useraddress_instance()
    source_type_set = set()
    sku_codes = []
    order_items = []
    for order in sale_trade.normal_orders:
        order_items.append({
            'sku_order_code': order.oid,
            'sku_id': order.outer_sku_id,
            'quantity': order.num,
            'object': 'OutwareOrderSku',
        })
        sku_codes.append(order.outer_sku_id)
        product_sku = ProductSku.objects.get(id=order.sku_id)
        model_product = product_sku.product.product_model
        source_type_set.add(model_product.source_type)

    vendor_codes = OutwareSku.objects.filter(sku_code__in=sku_codes)\
        .values_list('outware_supplier__vendor_code',flat=True)
    channel_maps = sdks.get_channelid_by_vendor_codes(vendor_codes)
    if not channel_maps or len(set(channel_maps.values())) > 1:
        raise Exception('同一订单只能有且只有一个channelid属性')

    if not source_type_set or len(source_type_set) > 1:
        raise Exception('商品对应货源来源类型不唯一：trade: %s, source_types: [%s]' % (sale_trade.tid, ','.join(source_type_set)))
    print 'source_type_set:', source_type_set
    order_type = constants.ORDER_TYPE_USUAL['code']
    if list(source_type_set)[0] == SaleProduct.SOURCE_BONDED:
        order_type = constants.ORDER_TYPE_CROSSBOADER['code']

    if list(source_type_set)[0] == SaleProduct.SOURCE_OUTSIDE:
        raise Exception('直邮模式暂不支持')

    params = {
        # 'store_code': warehouse.store_code,
        'order_number': sale_trade.tid,
        'order_create_time': sale_trade.created.strftime('%Y-%m-%d %H:%M:%S'),
        'pay_time': sale_trade.pay_time.strftime('%Y-%m-%d %H:%M:%S'),
        # 'order_type': order_type, # TODO@MERON　跨境订单不需要此字段，默认不接口内条件补填
        'channel_id': channel_maps.values()[0],
        'receiver_info': {
            'receiver_country': '中国',
            'receiver_province': address.receiver_state,
            'receiver_city': address.receiver_city,
            'receiver_area': address.receiver_district,
            'receiver_address': address.receiver_address,
            'receiver_name': address.receiver_name,
            'receiver_mobile': address.receiver_mobile,
            'receiver_phone': address.receiver_phone,
            # 'order_person_idname': address.receiver_mobile, # TODO 跨境需传
            # 'order_person_idcard': address.receiver_phone, # TODO 跨境需传
        },
        'order_items': order_items,
        'object': 'OutwareOrder',
    }

    # TODO@MERON, 2017.4.19 ,跨境订单默认只支持保税报关方式
    if order_type == constants.ORDER_TYPE_CROSSBOADER['code']:
        params['declare_type'] = constants.DECLARE_TYPE_BOUND['code']
        params['order_person_idname'] = address.receiver_name
        params['order_person_idcard'] = address.idcard_no
        # params['receiver_info']['receiver_identity']   = address.idcard_no

    dict_obj = DictObject().fresh_form_data(params)
    response = oms.create_order(order_code, store_code, order_type, dict_obj)

    return response


def push_outware_inbound_by_sale_refund(sale_refund):
    """ 创建销退单,　现只支持一个退货单创建一个销退入仓单 """

    warehouse = sale_refund.get_warehouse_object()
    sale_order = SaleOrder.objects.get(id=sale_refund.order_id)

    # TODO@meron 退货申请时需要客服判断具体时哪个供应商的商品,目前默认设置成最近一次供货的供应商
    ow_ordersku = OutwareOrderSku.objects.get(origin_skuorder_no=sale_order.oid)
    ow_sku = OutwareSku.objects.filter(sku_code=ow_ordersku.sku_code).order_by('-modified').first()
    vendor_code = ow_sku.outware_supplier.vendor_code
    channel_maps = sdks.get_channelid_by_vendor_codes([vendor_code])

    sale_supplier = ow_sku.outware_supplier
    params = {
        'store_code': warehouse.store_code,
        'order_code': sale_refund.refund_no,
        'vendor_code': vendor_code,
        'channel_id': channel_maps.values()[0],
        'order_type': constants.ORDER_REFUND['code'],
        'prev_order_code': ow_ordersku.union_order_code,
        'tms_order_code': sale_refund.sid,
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
            'batch_code': '', #ow_packagesku.batch_no, 当前批次号不确定，可以不传
            'object': 'OutwareInboundSku',
        }],
        'object': 'OutwareInboundOrder',
    }

    dict_obj = DictObject().fresh_form_data(params)
    response = pms.create_inbound_order(dict_obj.order_code, dict_obj.vendor_code, dict_obj)

    return response

