import datetime
from django.db.models import Q
from shopback.trades.models import MergeTrade

def cal_stage_old_customer(start,end,stage=5):
    
    trades = MergeTrade.objects.filter(pay_time__gt=start,pay_time__lt=end)
    buyer_cons = set()
    
    for trade in trades:
        buyer_cons.add(trade.receiver_mobile or trade.receiver_phone)
        
    dt = start
    for i in range(0,stage):
        df = dt - datetime.timedelta(30)
        vl = MergeTrade.objects.filter(Q(receiver_mobile__in=buyer_cons)|Q(receiver_phone__in=buyer_cons),pay_time__gt=df,pay_time__lt=dt)
        buyers = set()
        for t in vl:
            buyers.add(t.receiver_mobile or t.receiver_phone)
            
        print 'stage:',i,len(buyers)
        
        dt = df
        
        