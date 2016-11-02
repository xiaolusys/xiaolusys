# coding=utf-8
"""
fix the bug problem case run onece time only
2015-10-28 17:31:05 start
2015-10-28 15:32:08 end
"""
__author__ = 'jishu_linjie'

import datetime
import logging

logger = logging.getLogger(__name__)
from flashsale.pay.models import SaleRefund, SaleOrder


def fix_ref_exception():
    start_time = datetime.datetime(2015, 10, 28, 15, 32, 5)
    end_time = datetime.datetime(2015, 10, 28, 17, 31, 8)
    refunds = SaleRefund.objects.filter(created__gte=start_time, created__lte=end_time)
    print "deal with refund count  is :", refunds.count()
    for ref in refunds:
        order_id = ref.order_id
        print "order_id:", order_id, 'ref id:', ref.id
        try:
            order = SaleOrder.objects.get(id=order_id)
            trade = order.sale_trade
            ref.item_id = order.item_id
            ref.sku_id = order.sku_id
            ref.title = order.title
            ref.buyer_id = trade.buyer_id
            ref.charge = trade.charge
            ref.refund_num = order.num
            ref.mobile = trade.receiver_mobile
            ref.payment = order.payment
            ref.refund_fee = order.payment
            ref.save()
        except Exception, exc:
            logger.error(exc.message, exc_info=True)
            print order_id
            continue

