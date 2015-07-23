import sys
from datetime import datetime

from django.core.management import setup_environ
import settings
setup_environ(settings)

from shopback.trades.models import MergeTrade
from shopapp.weixin.models import WXOrder
from flashsale.pay.models import SaleTrade,SaleOrder
from flashsale.clickrebeta.models import StatisticsShopping

def calc_deep_num(mm,deep):
    
    mcount = 0
    for m,v in mm.iteritems():
        if v >= deep:
            mcount += 1

    return mcount
        

def calc_repeat(df,dt,deep=5,openid_set=None):

    queryset = MergeTrade.objects.filter(type__in=("wx","sale"))
    mts = queryset.filter(pay_time__range=(df,dt))
    
    sm  = {}
    mm  = {}
    uni_set = set([])
    #outer_ids = []

    for t in mts:
        wos = StatisticsShopping.objects.filter(wxorderid=t.tid)
        if wos.count() == 0:#wo.product_id in outer_ids:
            continue
        wo  = wos[0]
        if openid_set and wo.openid not in openid_set:
            continue

        tm = '%s-%s'%(t.pay_time.month,t.pay_time.day)
        if sm.has_key(tm):
            sm[tm].add(wo.openid)
        else:
            sm[tm] = set([wo.openid])

        uni_set.add(wo.openid)

    for s,m in sm.iteritems():
        for u in m:
            mm[u] = mm.get(u,0) + 1    
           
    total_num = len(uni_set)

    total_sm = 0
    for s,m in sm.iteritems():
        total_sm += len(m)

    for d in range(2,deep+1):
        
        mc = calc_deep_num(mm,d)
        print 'DEEP =',d,"%s/%s="%(mc,total_num),total_num and round(mc/(total_num*1.0),4) or 0    

    print df,"=>",dt,"%s-%s/%s="%(total_sm,total_num,total_num), total_num and round((total_sm-total_num)/(total_num*1.0),4) or 0

    
def calc_new_repeat():
    
    msd = datetime(2015,3,1)
    mft = datetime(2015,4,1)
    mtt = datetime(2015,5,1)
    mtf = datetime(2015,6,1)
    mtg = datetime(2015,6,16)

    mt3  = StatisticsShopping.objects.filter(shoptime__gt=msd,shoptime__lt=mft)
    mt4  = StatisticsShopping.objects.filter(shoptime__gt=mft,shoptime__lt=mtt)
    mt5  = StatisticsShopping.objects.filter(shoptime__gt=mtt,shoptime__lt=mtf)
    mt6  = StatisticsShopping.objects.filter(shoptime__gt=mtf,shoptime__lt=mtg)
    
    sm3    = set([o[0] for o in  mt3.values_list('openid')])
    sm4    = set([o[0] for o in  mt4.values_list('openid')])
    sm5    = set([o[0] for o in  mt5.values_list('openid')])
    sm6    = set([o[0] for o in  mt6.values_list('openid')])
    
    new_m4 = sm4 - sm3
    print "april stats:%s,%s"%(len(sm4),len(new_m4))
    s_m4 = len(new_m4)
    r_m5_m4 = len(sm5 & new_m4)
    r_m6_m4 = len(sm6 & new_m4)
    print "%s / %s = "%(r_m5_m4,s_m4),r_m5_m4 / (s_m4 * 1.00) , "%s / %s ="%(r_m6_m4, s_m4), r_m6_m4 / (s_m4 * 1.00)

    new_m5 = (sm5 - sm3 -sm4)
    print "may stats:%s,%s"%(len(sm5),len(new_m5))
    s_m5 = len(new_m5)
    r_m6_m5 = len(new_m5 & sm6)

    print "%s / %s ="%(r_m6_m5, s_m5),r_m6_m5 / (s_m5 * 1.00) 


def calc_same_repeat(mf,mt,deep=5):
    
    mft = datetime(mf.year,mf.month+1,1)
    mtt = datetime(mf.year,mf.month+1,1)
    mtf = datetime(mf.year,mf.month+1,16)
    mtg = datetime(mf.year,mf.month+3,16)

    mta  = StatisticsShopping.objects.filter(shoptime__gt=mf,shoptime__lt=mft)
    #mtb  = StatisticsShopping.objects.filter(shoptime__gt=mt,shoptime__lt=mtt)
    
    #mta = WXOrder.objects.filter(order_create_time__gt=mf,order_create_time__lt=mft)
    #mtb = WXOrder.objects.filter(order_create_time__gt=mt,order_create_time__lt=mtt)
    
    sma    = set([o[0] for o in  mta.values_list('openid')])
    #smb    = set([o[0] for o in  mtb.values_list('openid')])
    
    #smerge = sma - (sma - smb)

    #print '###############stage one %s - %s###############'%(mf,mft)
    #calc_repeat(mf,mtt,openid_set=smerge)

    #print '###############stage two %s - %s###############'%(mt,mtt)
    #calc_repeat(mt,mtt,openid_set=smerge)
    
    smerge = sma
    print '########### total count:%s,start:%s  ###########'%(len(smerge),datetime.now())
    #print '###############stage merge %s - %s###############'%(mft,mtt)
    #calc_repeat(mft,mtt,openid_set=smerge)

    print '###############stage merge %s - %s###############'%(mtt,mtf)
    calc_repeat(mtt,mtf,openid_set=smerge)


if __name__ == "__main__":
    
    if len(sys.argv) != 3:
        print >> sys.stderr, "usage: python *.py  <datefrom> <dateto>"
        sys.exit(1)
    
    df = datetime.strptime(sys.argv[1],"%Y-%m-%d")
    dt = datetime.strptime(sys.argv[2],"%Y-%m-%d")

    calc_repeat(df,dt)

#    calc_same_repeat(df,dt)
    
#    calc_new_repeat()
