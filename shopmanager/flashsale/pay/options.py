#-*- coding:utf8 -*-
import string, time, math, random
 
def uniqid(prefix='', more_entropy=False):
    m = time.time()
    uniqid = '%8x%05x' %(math.floor(m),(m-math.floor(m))*1000000)
    if more_entropy:
        valid_chars = list(set(string.hexdigits.lower()))
        entropy_string = ''
        for i in range(0,10,1):
            entropy_string += random.choice(valid_chars)
        uniqid = uniqid + entropy_string
    uniqid = prefix + uniqid
    return uniqid

import json
from urllib import urlopen
from django.http import Http404
from django.conf import settings

def get_user_unionid(code, 
                    appid=settings.WEIXIN_APPID, 
                    secret=settings.WEIXIN_SECRET):

    if settings.DEBUG:
        return ('oMt59uE55lLOV2KS6vYZ_d0dOl5c','')
    
    if not code :
        return ('','')

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

from django.forms import model_to_dict
from .models_addr import District

def getDistrictTree(province=None):

    dc_json = []
    fdist = District.objects.filter(grade=District.FIRST_STAGE)
    if province:
        fdist = fdist.filter(name=province)
        
    for fd in fdist:
        sdist = District.objects.filter(parent_id=fd.id)
        fd_json = model_to_dict(fd)
        fd_json['childs'] = []
        
        for sd in sdist:
            sd_json = model_to_dict(sd)
            sd_json['childs'] = []
            tdist = District.objects.filter(parent_id=sd.id)
            
            for td in tdist:
                sd_json['childs'].append(model_to_dict(td))
                
            fd_json['childs'].append(sd_json)
        
        dc_json.append(fd_json)
        
    return dc_json

from .models_addr import UserAddress

def getAddressByUserOrID(customer,id=None):
    
    if id:
        address_set = UserAddress.normal_objects.filter(cus_uid=customer.id,id=id)
        if address_set.count() > 0:
            return address_set[0]
        return None
    
    address_set = UserAddress.normal_objects.filter(cus_uid=customer.id)
    if address_set.filter(default=True).count() > 0:
        return address_set.filter(default=True)[0]
    elif address_set.count() > 0:
        return address_set[0]
    else:
        return None
