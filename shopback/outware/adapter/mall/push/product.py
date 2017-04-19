# coding: utf8
from __future__ import absolute_import, unicode_literals

from core.apis import DictObject

from pms.supplier.models import SaleProduct
from shopback.items.models import Product
from shopback.outware.fengchao import sdks
from ....adapter.ware.pull import pms
from .... import constants

from ....tasks import task_outware_union_supplier_and_sku

def push_ware_sku_by_saleproduct(sale_product):

    vendor_code = sale_product.sale_supplier.vendor_code

    success_skucode_list = []
    products = sale_product.item_products
    modelproduct = sale_product.model_product
    brand_name = ''
    if modelproduct and modelproduct.brand:
        brand_name = modelproduct.brand.brand_name

    # 是否十里洋场供应商
    is_slyc_vendor = vendor_code == sdks.FENGCHAO_SLYC_VENDOR_CODE

    for product in products:
        sku_type = constants.SKU_TYPE_PRODUCT['code']
        if product.type == Product.NO_SALE:
            sku_type = constants.SKU_TYPE_METARIAL['code']

        declare_type = constants.DECLARE_TYPE_NONE['code']
        if modelproduct.source_type == SaleProduct.SOURCE_BONDED:
            declare_type = constants.DECLARE_TYPE_BOUND['code']
        elif modelproduct.source_type == SaleProduct.SOURCE_OUTSIDE:
            declare_type = constants.DECLARE_TYPE_DIRECT['code']

        for sku in product.normal_skus:
            sku_code = sku.outer_id
            params = {
                'sku_code': sku_code,
                'bar_code': sku.supplier_skucode,
                'sku_name': product.name + sku.name,
                'sku_type': sku_type,
                'brand_name': brand_name,
                'is_batch_mgt': sale_product.is_batch_mgt_on,
                'is_xpire_mgt': sale_product.is_expire_mgt_on,
                'vdr_flag': sale_product.is_vendor_mgt_on,
                'shelf_life': sale_product.shelf_life_days,
                'specification': '', # 规格
                'color': '', #颜色
                'size': '',  #尺码
                'capacity': '', #内存容量
                'service_provider': '', #运营商
                'network_type': '', #网络类型
                # 'main_vendor': 1, # 是否主供应商,TODO@MERON
                # 'vdr_provide_barcode': 1, #是否提供条码, TODO@MERON
                'object': 'OutwareSku',
            }
            if is_slyc_vendor:
                # TODO@MENTION，厂家编码,十里洋场的需要填写,mfg_sku_code默认跟 sku_code一致
                params.update({
                    'mfg_sku_code': sku.supplier_skucode,
                })

            # TODO@MERON ,现默认所有SKU为商品类型，没有区分赠品包材
            dict_params = DictObject().fresh_form_data(params)
            resp = pms.create_sku_and_supplier(sku_code, vendor_code, sku_type, declare_type, dict_params)
            if resp.get('success'):
                success_skucode_list.append(sku_code)

    #　十秒后执行union操作
    task_outware_union_supplier_and_sku.apply_async(sku_codes=success_skucode_list,countdown=3)

    return success_skucode_list

