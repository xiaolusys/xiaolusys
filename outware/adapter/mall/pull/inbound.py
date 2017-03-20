# coding: utf8
from __future__ import absolute_import, unicode_literals

from ....models import OutwareInboundOrder, OutwareInboundSku

def update_forecast_inbound_by_outware_inbound(order_code, dict_obj):
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
          "order_type": 601,
          "order_code": "fid201702055896d6ecf0f66",
          "store_code": "SZWH01"
        }
    """
    pass



def update_return_store_by_outware_packages(return_code, dict_obj):
    # TODO@MERON暂时不考录退仓
    pass

