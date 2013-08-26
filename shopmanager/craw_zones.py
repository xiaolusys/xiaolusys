from django.db.models import Q
from shopapp.shipclassify.models import ClassifyZone
from shopback.trades.models import MergeTrade

def get_addr_zones(state,city,district):
    lstate = len(state)>1 and state[0:2] or ''
    lcity  = len(city)>1  and city[0:2]  or ''
    ldistrict  = len(district)>1  and district[0:2]  or ''
    
    if district:
        czones = ClassifyZone.objects.filter(Q(city__startswith=lcity)|Q(district__startwith=ldistrict),state__startswith=lstate)
        
        if czones.count() == 1:
            return czones[0].zone
        
        for czone in czones:
            if czone.city == district or czone.district == district:
                return czone.zone
        
    if city:
        czones = ClassifyZone.objects.filter(state__startswith=lstate,
                                                  city__startswith=lcity,district=='')
        if czones.count():
            return czone[0].zone
    
    return ''

def cal_zones():
    trades = MergeTrade.objects.all()
    zones_hash = {}
    
    for trade in trades:
        state = trade.receiver_state
        city  = trade.receiver_city
        district = trade.receiver_district
        zone = get_addr_zones(state,city,district)
        if zone:
            if zones_hash.has_key(zones_hash):
                zones_hash[zone] += 1
            else:
                zones_hash[zone] = 1
                
    zones_list =  sorted(zones_hash.items(),key=lambda d:d[1],reverse=True)
    for z,n in zones_list:
        
        print z,n
         