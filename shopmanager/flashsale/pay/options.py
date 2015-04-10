import json
from urllib import urlopen

from django.http import Http404
from django.conf import settings

def get_user_unionid(code, 
                    appid=settings.WEIXIN_APPID, 
                    secret=settings.WEIXIN_SECRET):

    if settings.DEBUG:
        return 'oMt59uE55lLOV2KS6vYZ_d0dOl5c'
    
    if not code :
        return ''

    url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code'
    get_openid_url = url % (appid, secret, code)
    r = urlopen(get_openid_url).read()
    r = json.loads(r)
    
    if r.has_key("errcode"):
        raise Exception(r['errmsg'])
    
    return (r.get('openid'),r.get('unionid'))

from django.contrib.auth.models import User as DjangoUser
from shopback.users.models import User

def getOrCreateSaleSeller():
    
    sellers = User.objects.filter(type=User.SHOP_TYPE_SALE)
    if sellers.count() > 0:
        return sellers[0]
    
    user,state = DjangoUser.objects.get_or_create(username='flashsale')
    seller,state = User.objects.get_or_create(user=user,type=User.SHOP_TYPE_SALE)
    seller.nick  = u'小鹿美美特卖平台'
    seller.save()
    
    return seller
