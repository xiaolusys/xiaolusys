# coding=utf-8
from flashsale.pay.signals import signal_saletrade_refund_post
from flashsale.pay.models import SaleRefund


def triger_refund_record(sender, obj, **kwargs):
    from tasks import taskRefundRecord
    taskRefundRecord.delay(obj)


signal_saletrade_refund_post.connect(triger_refund_record, sender=SaleRefund)
