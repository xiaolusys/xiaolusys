import datetime
from django.db.models import Q
from shopback.trades.models import MergeTrade

def cal_stage_old_customer(start,end,stage=5):
    
    trades = MergeTrade.objects.filter(pay_time__gt=start,pay_time__lt=end)
    buyer_cons = set()
    add_set = set()

    for trade in trades:
        if trade.receiver_mobile:
            buyer_cons.add(trade.receiver_mobile)
    
    print 'total:',len(buyer_cons)

    dt = start
    for i in range(0,stage):
        df = dt - datetime.timedelta(30)

        vl = MergeTrade.objects.filter(receiver_mobile__in=buyer_cons,pay_time__gt=df,pay_time__lt=dt)

        buyers = set()
        for t in vl:
            buyers.add(t.receiver_mobile)
            
        print 'stage:',i,len(buyers-add_set)
        add_set.update(buyers)
        
        dt = df

    print 'rebuy:',len(add_set)
        
        
