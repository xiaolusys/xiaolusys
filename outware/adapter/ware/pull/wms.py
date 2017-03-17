# coding: utf8
from __future__ import absolute_import, unicode_literals

from ....models import OutwareSkuStock


def get_order_packages(origin_skuorder_codes):
    pass

def get_skustocks(sku_codes):
    # 创建销退订单接口
    ow_skus = OutwareSkuStock.objects.filter(sku_code__in=sku_codes)
    return []