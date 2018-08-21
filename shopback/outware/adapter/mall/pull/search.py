# coding: utf8
from __future__ import absolute_import, unicode_literals

from ....models import OutwareSku, OutwareInboundOrder, OutwareSupplier
from shopback.items.models import ProductSku

def get_outware_inbound_by_code(inbound_code):

    ow_inbound = OutwareInboundOrder.objects.filter(inbound_code=inbound_code).first()
    if not ow_inbound:
        return {}

    data = ow_inbound.extras.get('data') or {}
    vendor_code = data.get('vendor_code', '')
    for sku_item in data.get('order_items', []):
        sku_code = sku_item['sku_id']
        ow_sku = OutwareSku.objects.get(
            outware_supplier__vendor_code=vendor_code, sku_code=sku_code)
        pd_sku = ProductSku.objects.get(outer_id=sku_code)
        sku_item['sku_code'] = sku_code
        sku_item['sku_img'] = pd_sku.product.pic_path
        sku_item['is_batch_mgt']  = ow_sku.is_batch_mgt_on
        sku_item['is_expire_mgt'] = ow_sku.is_expire_mgt_on
        sku_item['is_vendor_mgt'] = ow_sku.is_vendor_mgt_on
        sku_item['shelf_life']    = ow_sku.shelf_life_days
        sku_item['is_pushed_ok']  = ow_sku and ow_sku.is_pushed_ok or False,
        sku_item['is_unioned']    = ow_sku and ow_sku.is_unioned or False,

    data['is_received'] = ow_inbound.is_pushed_ok

    return data

def get_outware_sku_by_code(inbound_code):

    ow_inbound = OutwareInboundOrder.objects.filter(inbound_code=inbound_code).first()
    if not ow_inbound:
        return {}

    data = ow_inbound.extras.get('data') or {}
    vendor_code = data.get('vendor_code', '')
    for sku_item in data.get('order_items', []):
        sku_code = sku_item['sku_id']
        ow_sku = OutwareSku.objects.get(
            outware_supplier__vendor_code=vendor_code, sku_code=sku_code)
        pd_sku = ProductSku.objects.get(outer_id=sku_code)
        sku_item['sku_code'] = sku_code

    data['is_received'] = ow_inbound.is_pushed_ok

    return data