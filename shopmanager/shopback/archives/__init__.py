from shopback.archives.models import DepositeDistrict


def initial_district():
    
    s='ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for i in xrange(0,26):
        
        for j in xrange(1,7):
        
            for k in xrange(1,17):
            
                DepositeDistrict.objects.get_or_create(district_no='%d'%k,parent_no='%s%d'%(s[i],j))