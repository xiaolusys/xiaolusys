import datetime
from shopback.trades.models import MergeTrade
from shopapp.shipclassify.options import get_addr_zones

def classify_to_branch():
    
    zones = ClassifyZone.objects.all()
    for zone in zones:
        tl = zone.zone.split()
        name = tl[0].strip()
        code = len(tl)>1 and tl[1] or ''
        branch,state = BranchZone.objects.get_or_create(name=name)
        if state:
            branch.code = code or ''
            branch.save()
        
        zone.branch = branch
        zone.save()
        

def cal_zones():
    trades = MergeTrade.objects.filter(pay_time__gt=datetime.datetime(2013,7,1))
    zones_hash = {}
    
    for trade in trades:
        state = trade.receiver_state
        city  = trade.receiver_city
        district = trade.receiver_district
        zone = ''
        try:
            zone = get_addr_zones(state,city,district) 
        except Exception,exc:
            print exc.message,state,city,district
        if zone:
            if zones_hash.has_key(zone.name):
                zones_hash[zone] += 1
            else:
                zones_hash[zone] = 1
                
    zones_list =  sorted(zones_hash.items(),key=lambda d:d[1],reverse=True)
    for z,n in zones_list:
        
        print z,n
         
