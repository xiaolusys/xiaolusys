# coding=utf-8
from flashsale.pay.models import TradeCharge, SaleTrade
from flashsale.pay.tasks import confirmTradeChargeTask
from datetime import datetime
import hashlib

def add_charge(order_no):
    strade = SaleTrade.objects.get(tid=order_no)
    tc = TradeCharge()
    tc.order_no = order_no
    tc.charge_id = 'ch_' + hashlib.sha256(order_no).hexdigest()[:24]
    tc.paid = True
    tc.refunded = False
    tc.channel = 'alipay_wap'
    tc.amount = str(strade.payment * 100)
    tc.currency = 'cny'
    tc.transaction_no = datetime.now().strftime('%Y%m%d%H%M%S00')
    tc.time_paid = datetime.now()
    tc.save()
    return tc

def notify(tcharge):
    charge_time = tcharge.time_paid
    strade = SaleTrade.objects.get(tid=tcharge.order_no)
    confirmTradeChargeTask(strade.id, charge_time=charge_time)

#t= add_charge('xd16032956fa448dcf8e4')
#notify(t)

if __name__ == '__main__':
    from flashsale.pay.test.set_order_paid import *
    from flashsale.pay.models import TradeCharge
    s ='xd16040256ff63cd22d1e'
    #t = add_charge(s)
    t =TradeCharge.objects.get(order_no=s)
    notify(t)
