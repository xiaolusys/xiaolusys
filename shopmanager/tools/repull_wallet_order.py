import sys
import time
import datetime

from django.core.management import setup_environ
import settings
setup_environ(settings)

from flashsale.xiaolumm.models import CarryLog
from flashsale.pay.models import SaleTrade
from flashsale.pay.tasks import confirmTradeChargeTask

def update_wallet_order(target_date):
    
    clogs = CarryLog.objects.filter(carry_date=target_date,
                                    log_type=CarryLog.ORDER_BUY,status='confirmed')

    oids = [o[0] for o in clogs.values_list('order_num')]
    oset = set([])
    for o in oids:
        if o in oset:
            print 'repeat payment:',o 
        else:
            oset.add(o)
    
    print 'total distinct order num:',len(oset)
    strades = SaleTrade.objects.filter(status__in=(0,1,7),id__in=oset)
    for st in strades:
        try:
            confirmTradeChargeTask(st.id,charge_time=datetime.datetime.now())
        except:
            print 'exc:',exc.message
        print 'update trade:',st.id,st.tid


if __name__ == "__main__":
    
    if len(sys.argv) != 2:
        print >> sys.stderr, "usage: python *.py <dt>"
    
    target_date = datetime.datetime.strptime(sys.argv[1],'%Y-%m-%d')
    update_wallet_order(target_date)
    
    
