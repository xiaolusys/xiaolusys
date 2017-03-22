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
          ],dict_obj
          "order_type": 601,
          "order_code": "fid201702055896d6ecf0f66",
          "store_code": "SZWH01"
        }
    """
    from flashsale.dinghuo.models import InBound, InBoundDetail
    from shopback.trades.models import ProductSku
    ibds = []
    for line in dict_obj['inbound_skus']:
        sku = ProductSku.objects.filter(outer_id=line['sku_code']).first()
        ibd = InBoundDetail.create(sku, line['pull_good_qty'], line.get('pull_bad_qty', 0))
        ibds.append(ibd)
    InBound.create(ibds, order_code, 'fengchao')


def update_return_store_by_outware_packages(return_code, dict_obj):
    # TODO@MERON暂时不考录退仓
    pass

