# coding: utf8
from __future__ import absolute_import, unicode_literals

from flashsale.pay.models import SaleTrade, SaleOrder, SaleRefund
from ....models import OutwareOrder, OutwareOrderSku

def update_saletrade_by_outware_packages(order_code, dict_obj):
    """
    order_code: xd16111358284ace3a74f
    dict_obj:  {
          "packages": [
            {
              "package_items": [
                {
                  "sku_qty": 2,
                  "object": "OutwarePackageSku",
                  "sku_code": "SP111111AA",
                  "batch_no": "AJEV"
                }
              ],
              "object": "OutwarePackage",
              "carrier_code": "YUNDA",
              "logistics_no": "9867542222",
              "store_code": "SZWH01"
            }
          ],
          "order_type": 401,
          "order_code": "xd16111358284ace3a74f",
          "object": "OutwareObject"
        }
    """
    pass
    # outware_skuorders = OutwareOrderSku.objects.filter(union_order_code=order_code)
    # for sku_order in outware_skuorders:
    #     so = SaleOrder.objects.get(oid=sku_order.origin_skuorder_no)
    #     so.finish_sent()


def update_salerefund_by_outware_inbound(order_code, dict_obj):
    """
    order_code: fid201702055896d6ecf0f66
    dict_obj:{
          "object": "OutwareInboundOrder",
          "inbound_skus": [
            {
              "object": "OutwareInboundSku",
              "pull_bad_qty": 1,
              "sku_code": "SP111111AA",
              "batch_no": "AJEV",
              "pull_good_qty": 2
            }
          ],
          "order_type": 501,
          "order_code": "fid201702055896d6ecf0f66",
          "store_code": "SZWH01"
        }
    """
    pass


def update_outware_order_by_goodlack_notify(order_code, dict_obj):
    """
    order_code: xd16111358284ace3a74f
    dict_obj: {
          "object": "OutWareLackOrder",
          "order_code": "xd16111358284ace3a74f",
          "order_type": 701,
          "lack_goods": [
            {
              "lack_qty": 2,
              "sku_name": "ABCD",
              "sku_code": "SP11111AAA",
              "object": "OutWareLackOrderGood"
            }
          ]
        }
    """
    pass