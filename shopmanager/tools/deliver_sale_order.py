import sys
import time
import datetime

from django.core.management import setup_environ
import settings
setup_environ(settings)

from shopback.trades.models import MergeTrade,MergeOrder

def deliver(outer_ids=[]):
    mos = MergeOrder.objects.filter(merge_trade__type="wx",outer_id__in=outer_ids,
                                    merge_trade__sys_status__in=("WAIT_PREPARE_SEND"
                                                                 ,"WAIT_AUDIT"
                                                                 ,"REGULAR_REMAIN"))
    
    tids = set([o.merge_trade.id for o in mos])
    print "update trades count:",len(tids)

    for tid in tids:
        t = MergeTrade.objects.get(id=tid)
        if (t.inuse_orders.count() > 1 or 
            not t.logistics_company or 
            t.has_reason_code('1') or 
            t.has_reason_code('2') or
            t.has_reason_code('7') or
            t.has_reason_code('8') or
            t.has_reason_code('11')):
            t.sys_status="WAIT_AUDIT"
        else:
            t.sys_status="WAIT_PREPARE_SEND"
            t.reason_code = ""
            t.has_out_stock = ""
        t.save()
    
if __name__ == "__main__":
    
    print sys.argv
    if len(sys.argv) != 2:
        print >> sys.stderr, "usage: python *.py <outer_ids> "
    
    outer_ids = sys.argv[1].split(',')
    
    deliver(outer_ids=outer_ids)
    
    
