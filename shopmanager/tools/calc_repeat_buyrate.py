import sys
from datetime import datetime

from django.core.management import setup_environ
import settings
setup_environ(settings)

from shopback.trades.models import MergeTrade
from shopapp.weixin.models import WXOrder

def calc_deep_num(mm,deep):
    
    mcount = 0
    for m,v in mm.iteritems():
        if v >= deep:
            mcount += 1

    return mcount
        

def calc_repeat(df,dt,deep=5):

    queryset = MergeTrade.objects.filter(type="wx")
    
    mts = queryset.filter(created__gt=df,created__lt=dt)

    sm  = {}
    mm  = {}
    uni_set = set([])
    outer_ids = []
    
    for t in mts:
        wo = WXOrder.objects.get(order_id=t.tid)
        if wo.product_id in outer_ids:
            continue
        tm = '%s-%s'%(t.pay_time.month,t.pay_time.day)
        if sm.has_key(tm):
            sm[tm].add(wo.buyer_openid)
        else:
            sm[tm] = set([wo.buyer_openid])

        uni_set.add(wo.buyer_openid)

    for s,m in sm.iteritems():
        for u in m:
            mm[u] = mm.get(u,0) + 1    
           
    total_num = len(uni_set)
 
    total_sm = 0
    for s,m in sm.iteritems():
        total_sm += len(m)
    
    for d in range(2,deep+1):
        
        mc = calc_deep_num(mm,d)
        print 'DEEP =',d,"%s/%s="%(mc,total_num),round(mc/(total_num*1.0),2)    
    print df,"=>",dt,"%s-%s/%s="%(total_sm,total_num,total_num),round((total_sm-total_num)/(total_num*1.0),2)
    

if __name__ == "__main__":
    
    if len(sys.argv) != 3:
        print >> sys.stderr, "usage: python *.py  <datefrom> <dateto>"
        sys.exit(1)
    
    df = datetime.strptime(sys.argv[1],"%Y-%m-%d")
    dt = datetime.strptime(sys.argv[2],"%Y-%m-%d")

    calc_repeat(df,dt)

