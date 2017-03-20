# coding: utf8
from __future__ import absolute_import, unicode_literals

from core.apis import DictObject
from ....adapter.ware.pull import pms
from .... import constants

from ....tasks import task_outware_union_supplier_and_sku

def push_ware_sku_by_saleproduct(sale_product):

    vendor_code = sale_product.sale_supplier.vendor_code

    success_skucode_list = []
    products = sale_product.item_products
    for product in products:
        for sku in product.normal_skus:
            sku_code = sku.outer_id
            params = {
                'sku_code': sku_code,
                'bar_code': sku.supplier_skucode,
                'sku_name': product.name + sku.name,
                'sku_type': constants.SKU_TYPE_PRODUCT['code'],
                'object': 'OutwareSku',
                # 'is_xpire_mgt': True, #保质期管理
                # 'shelf_life': ''
            }
            # TODO@MERON ,现默认所有SKU为商品类型，没有区分赠品包材
            dict_params = DictObject().fresh_form_data(params)
            resp = pms.create_sku_and_supplier(sku_code, vendor_code, dict_params)
            if resp.get('success'):
                success_skucode_list.append(sku_code)

    #　十秒后执行union操作
    task_outware_union_supplier_and_sku.apply_async(countdown=3)

    return success_skucode_list

