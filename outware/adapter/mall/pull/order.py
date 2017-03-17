# coding: utf8
from __future__ import absolute_import, unicode_literals

from flashsale.pay.models import SaleTrade, SaleOrder, SaleRefund
from ....models import OutwareOrder, OutwareOrderSku

def update_saletrade_by_outware_packages(order_code, dict_obj):

    outware_skuorders = OutwareOrderSku.objects.filter(union_order_code=order_code)
    for sku_order in outware_skuorders:
        so = SaleOrder.objects.get(oid=sku_order.origin_skuorder_no)
        so.finish_sent()


def update_salerefund_by_outware_inbound(order_code, dict_obj):
    pass


def update_outware_order_by_goodlack_notify(order_code, dict_obj):
    pass