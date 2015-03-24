from django.core.management import setup_environ
import settings
setup_environ(settings)

import datetime
from shopapp.weixin.models import WeiXinUser,SampleOrder,VipCode
from shopapp.weixin_sales.models import WeixinLinkClicks

def dumps():
    
    mobiles = []
    sos = SampleOrder.objects.filter(status=0,created__gt=datetime.datetime(2015,3,23),created__lt=datetime.datetime(2015,3,24),)
    print 'sos len:',sos.count()
    cnt = 0 
    for m in sos:
        wxusers = WeiXinUser.objects.filter(openid=m.user_openid,charge_status=WeiXinUser.UNCHARGE)
        if wxusers.count() > 0:
            wxuser = wxusers[0]
            
            mobiles.append(wxuser.mobile)
            cnt += 1
            if cnt % 1000 == 0:
                print cnt
                
    return mobiles

if __name__ == "__main__":
    
    rmobiles = dumps()

    with open('/tmp/dumps-mobiles-15-03.txt','w+') as f:
        for m in rmobiles:
            try:
                print >> f,m,','
            except:
                print m 
