from django.db.models import Q
from shopapp.shipclassify.models import ClassifyZone,BranchZone


def get_addr_zones(s,c,d):
    lstate = len(s)>1 and s[0:2] or ''
    lcity  = len(c)>1  and c[0:2]  or ''
    ldistrict  = len(d)>1  and d[0:2]  or ''

    if d:
        czones = ClassifyZone.objects.filter(Q(city__startswith=ldistrict)|Q(district__startswith=ldistrict),state__startswith=lstate)
        if czones.count() == 1:
            return czones[0].branch
        
        for czone in czones:
            if czone.city == d or czone.district == d:
                return czone.branch
        
    if c:
        czones = ClassifyZone.objects.filter(state__startswith=lstate,
                                                  city__startswith=lcity,district='')
        if czones.count()==1:
            return czones[0].branch

        for czone in czones:
            if czone.city == c:
                return czone.branch
    
    if s:
        czones = ClassifyZone.objects.filter(state__startswith=lstate,
                                                  city='',district='')
        if czones.count()==1:
            return czones[0].branch

        for czone in czones:
            if czone.state == s:
                return czone.branch
    
    return None