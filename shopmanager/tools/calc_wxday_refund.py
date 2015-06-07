import sys
import datetime 

from django.core.management import setup_environ
import settings
setup_environ(settings)

from shopback.trades.models import MergeTrade
from shopback.refunds.models import Refund
from shopapp.weixin.models import WXOrder

def calc_day_refund(tdate):
    
    df = datetime.datetime(tdate.year,tdate.month,tdate.day,0,0,0)
    dt = datetime.datetime(tdate.year,tdate.month,tdate.day,23,59,59)
    
    mts = MergeTrade.objects.filter(type=MergeTrade.WX_TYPE,pay_time__range=(df,dt))
    refund_num = mts.filter(sys_status__in=(MergeTrade.INVALID_STATUS,MergeTrade.EMPTY_STATUS)).count()
    
    unmts = mts.exclude(sys_status__in=(MergeTrade.INVALID_STATUS,MergeTrade.EMPTY_STATUS)).values('tid').distinct()
    tids  = [ t['tid'] for t in unmts]
    
    
    refund_num += Refund.objects.filter(tid__in=tids).exclude(status__in=(Refund.NO_REFUND,Refund.REFUND_CLOSED)).values('tid').distinct().count()
    
    print tdate.date(),refund_num

if __name__ == "__main__":
    
    if len(sys.argv) != 3:
        print >> sys.stderr, "usage: python *.py  <datefrom> <dateto>"
        sys.exit(1)
    
    df = datetime.datetime.strptime(sys.argv[1],"%Y-%m-%d")
    dt = datetime.datetime.strptime(sys.argv[2],"%Y-%m-%d")
    
    today = datetime.datetime.now()
    delta = dt - df
    
    for d in range(1,delta.days):
        target_date = today - datetime.timedelta(days=d)
        calc_day_refund(target_date)