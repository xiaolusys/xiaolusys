from django.core.management import setup_environ
import settings
setup_environ(settings)

import datetime
from shopapp.weixin.models import WeiXinUser,SampleOrder,VipCode
from shopapp.weixin_sales.models import WeixinLinkClicks,WeixinLinkShare

def dumpsa():
    
    mobiles = []
    sos = SampleOrder.objects.filter(status__gt=60).exclude(status=69).exclude(status=79)
    print 'sos len:',sos.count()
    cnt = 0 
    for m in sos:
        wxusers  = WeiXinUser.objects.filter(openid=m.user_openid)#,charge_status=WeiXinUser.UNCHARGE)
        if wxusers.count() > 0:
            wxuser = wxusers[0]
            #vipcodes = VipCode.objects.filter(owner_openid=wxuser)
            #if vipcodes.count() == 0 or vipcodes[0].usage_count == 0:
            #    continue
            mobiles.append(wxuser.mobile)
            cnt += 1
            if cnt % 1000 == 0:
                print cnt
                
    return mobiles

def dumpsb():
    
    mobiles = []
    vipcodes = VipCode.objects.filter(usage_count__gt=0)
    print 'vipcode count:',vipcodes.count()
    cnt = 0 
    for m in vipcodes:
        wxusers  = WeiXinUser.objects.filter(id=m.owner_openid.id,charge_status=WeiXinUser.UNCHARGE)
        if wxusers.count() > 0:
            wxuser = wxusers[0]
            
            mobiles.append(wxuser.mobile)
            cnt += 1
            if cnt % 1000 == 0:
                print cnt
                
    return mobiles


def dumpsc():
    
    mobiles = []
    wlcs = WeixinLinkShare.objects.values_list('user_openid')
    print 'clicker count:',len(wlcs)
    wlcs = set([l[0] for l in wlcs])
    cnt = 0 

    for m in wlcs:
        wxusers  = WeiXinUser.objects.filter(openid=m,charge_status=WeiXinUser.UNCHARGE)
        if wxusers.count() > 0:
            wxuser = wxusers[0]
            
            mobiles.append(wxuser.mobile)
            cnt += 1
            if cnt % 1000 == 0:
                print cnt
                
    return mobiles

if __name__ == "__main__":
    
    rmobiles = dumpsa()

    with open('/tmp/dumps-mobiles-15-03-31-a.txt','w+') as f:
        for m in rmobiles:
            try:
                print >> f,m,','
            except:
                print m 
