import sys
import time
import datetime

from django.core.management import setup_environ
import settings
setup_environ(settings)

from shopback.trades.models import MergeTrade,MergeOrder

def regular(outer_ids=[],remind_time=datetime.datetime.now()):
    mos = MergeOrder.objects.filter(merge_trade__type="wx",outer_id__in=outer_ids,
                                    merge_trade__sys_status__in=("WAIT_PREPARE_SEND","WAIT_AUDIT"))
    
    tids = set([o.merge_trade.id for o in mos])
    print "update trades count:",len(tids)

    MergeTrade.objects.filter(id__in=tids,sys_status__in=("WAIT_PREPARE_SEND","WAIT_AUDIT"))\
        .update(sys_status="REGULAR_REMAIN",remind_time=remind_time)
    
    
if __name__ == "__main__":
    
    if len(sys.argv) != 3:
        print >> sys.stderr, "usage: python *.py <outer_ids> <regular_days>"
        return
    
    outer_ids = sys.argv[1].split(',')
    regular_days = int(sys.argv[2])
    
    print outer_ids , regular_days
    
    today = datetime.datetime.now()
    regular_data = datetime.datetime(today.year,today.month,today.day) + datetime.timedelta(days=regular_days)
    
    regular(outer_ids=outer_ids,remind_time=regular_data)

    
