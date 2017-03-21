# coding: utf8
from __future__ import absolute_import, unicode_literals

from shopback.items.models import ProductSku
from shopback.outware.adapter.ware.pull import pms
from .... import constants

from core.apis import DictObject

def push_outware_inbound_by_forecast_order(forecast_inbound_order):
    porder_set = forecast_inbound_order.relate_order_set
    if porder_set.count() > 1:
        raise Exception('推送入仓单目前只支持一个单位的采购单分单入仓')

    supplier = forecast_inbound_order.supplier
    warehouse = forecast_inbound_order.get_warehouse_object()
    params ={
        'store_code': warehouse.store_code,
        'order_code': forecast_inbound_order.forecast_no,
        'vendor_code': supplier.vendor_code,
        'order_type': constants.ORDER_PURCHASE['code'],
        'tms_order_code': forecast_inbound_order.express_no,
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
        'order_items': [],
        'object': 'OutwareInboundOrder',
    }

    normal_details = forecast_inbound_order.normal_details
    normal_sku_ids = list(normal_details.values_list('sku_id', flat=True))

    po_order = porder_set.first()
    productsku = dict(ProductSku.objects.in_bulk(normal_sku_ids))
    for detail in normal_details:
        params['order_items'].append({
            'sku_id': productsku[detail.sku_id].outer_id,
            'sku_name': detail.product_name,
            'quantity': detail.forecast_arrive_num,
            'batch_code': po_order.batch_no,
            'object': 'OutwareInboundSku',
        })
    # TODO@MERON目前预测暂未支持批次号问题，这里目前只去取first采购单的批次号,后期需要改正过来
    dict_obj = DictObject().fresh_form_data(params)
    response = pms.create_inbound_order(dict_obj.order_code, dict_obj.vendor_code, dict_obj)

    return response




