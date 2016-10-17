# coding:utf-8
from django.core.management import setup_environ
import settings

setup_environ(settings)

from django.conf import settings

from flashsale.pay.tasks import notifyTradeRefundTask
from core.options import log_action,CHANGE
from flashsale.pay.models import SaleTrade, SaleRefund

import pingpp

sfs = SaleRefund.objects.filter(status=SaleRefund.REFUND_APPROVE)
cnt = 0
for obj  in sfs:
    try:
        strade = SaleTrade.objects.get(id=obj.trade_id)
        pingpp.api_key = settings.PINGPP_APPKEY
        ch = pingpp.Charge.retrieve(strade.charge)
        rf = ch.refunds.retrieve(obj.refund_id)
        if rf.status == 'failed':
            rf = ch.refunds.create(description=obj.get_refund_desc(),
                                   amount=int(obj.refund_fee * 100))
            obj.refund_id = rf.id
            obj.save()
        else:
            notifyTradeRefundTask(rf)
        log_action(641, obj, CHANGE, 'auto refund:refund=%s' % rf.id)
    except Exception,exc:
        print obj.id, strade.tid
    cnt += 1
    print obj.id
    if cnt % 50 == 0:
        print '=======>',cnt