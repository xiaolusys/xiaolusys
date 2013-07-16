from shopback.trades.models import MergeTrade
trades = MergeTrade.objects.filter(status='TRADE_FINISHED')

all_set = set()
ids = ('2115DD5BZ6','2115DD5','0112BK1','3112BK9','0112BK3','3112BKF2','6170112DB2','6173115DB3','3115DB3','3116DM7')
with open('/tmp/crawsms-2013-07.txt','w+') as f:
    for t in trades:
        mobile = t.receiver_mobile
        if mobile in all_set:
            continue
    
        ss = set()
        tds = MergeTrade.objects.filter(receiver_mobile=t.receiver_mobile,status="TRADE_FINISHED")
        for td in tds:
            for o in td.inuse_orders:
                if o.outer_id in ids:
                    ss.add(o.outer_id)
    
        if len(ss)==0:
            print >>f,mobile

        all_set.add(mobile)


    
        