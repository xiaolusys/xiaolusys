# coding: utf8
from __future__ import absolute_import, unicode_literals

from ....models import (OutwareAccount, OutwareSkuStock, OutwarePackage,
                        OutwarePackageSku, OutwareOrder, OutwareOrderSku)
from core.apis.models import DictObject

from .... import constants
from ....utils import action_decorator

def get_order_packages(origin_skuorder_codes):
    # 找出sku_code　对应所有的packages
    sku_orders = OutwareOrderSku.objects.filter(origin_skuorder_code__in=origin_skuorder_codes)
    union_order_codes = sku_orders.values_list('union_order_code', flat=True).distinct()
    if len(union_order_codes) == 0:
        return []

    package_list = []
    packages = OutwarePackage.objects.filter(package_order_code__in=union_order_codes).values_list('extras', flat=True)
    for package in packages:
        package_list.append(
            DictObject().fresh_form_data(package.extras['data'])
        )

    return packages


def get_skustocks(sku_codes):
    # 创建销退订单接口

    sku_dicts = {}
    ow_skus = OutwareSkuStock.objects.filter(sku_code__in=sku_codes).values(
        'sku_code',
        'push_sku_good_qty',
        'push_sku_bad_qty',
        'pull_good_available_qty',
        'pull_good_lock_qty',
        'pull_bad_qty',
        'paid_num',
        'package_num',
        'refund_num',
        'adjust_num'
    )

    for sku_dict in ow_skus:
        sku_dict['object'] = 'OutwareSkuStock'
        sku_dicts[sku_dict['sku_code']] = DictObject().fresh_form_data(sku_dict)

    return sku_dicts


def get_outware_stock(sku_codes, vendor_code=None):

    from outware.fengchao import sdks
    inventorys = sdks.get_skustock_by_qureyparams(sku_codes, vendor_code=vendor_code)

    for inventory in inventorys:
        pass


    return []

