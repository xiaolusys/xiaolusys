from django.db.models import Q
from shopapp.shipclassify.models import ClassifyZone
from shopback.trades.models import MergeTrade

def get_addr_zones(s,c,d):
    lstate = len(s)>1 and s[0:2] or ''
    lcity  = len(c)>1  and c[0:2]  or ''
    ldistrict  = len(d)>1  and d[0:2]  or ''
    
    if d:
        czones = ClassifyZone.objects.filter(Q(city__startswith=lcity)|Q(district__startswith=ldistrict),state__startswith=lstate)
        
        if czones.count() == 1:
            return czones[0].zone
        
        for czone in czones:
            if czone.city == d or czone.district == d:
                return czone.zone
        
    if c:
        czones = ClassifyZone.objects.filter(state__startswith=lstate,
                                                  city__startswith=lcity,district='')
        if czones.count():
            return czones[0].zone
    
    return ''

def cal_zones():
    trades = MergeTrade.objects.all()
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
            if zones_hash.has_key(zone):
                zones_hash[zone] += 1
            else:
                zones_hash[zone] = 1
                
    zones_list =  sorted(zones_hash.items(),key=lambda d:d[1],reverse=True)
    for z,n in zones_list:
        
        print z,n
         
