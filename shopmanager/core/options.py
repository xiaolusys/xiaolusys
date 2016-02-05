__author__ = 'imeron'
import re
import json
import urllib
from django.conf import settings
from django.contrib.admin.models import LogEntry,User, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType

def log_action(user_id,obj,action,msg):
    try:
        LogEntry.objects.log_action(
                user_id = user_id,
                content_type_id = ContentType.objects.get_for_model(obj).id,
                object_id = obj.id,
                object_repr = repr(obj),
                change_message = msg,
                action_flag = action,
            )
    except Exception,exc:
        import logging 
        logger =  logging.getLogger('django.request')
        logger.error(exc.message,exc_info=True)
    

def get_cookie_openid(cookies,appid):
    x = cookies.get('sopenid','').split('|')
    y = cookies.get('sunionid','').split('|')
    if len(x) < 2 or len(y) <2 or x[0] != y[0] or y[0] != appid:
        return ('','')
    return (x[1], y[1])

def get_user_unionid(code, 
                    appid='', 
                    secret='',
                    request=None):

    debug_m   = settings.DEBUG
    content   = request and request.REQUEST or {}
    if not debug_m and request: 
        debug_m = content.get('debug')
    if debug_m:
        openid  = content.get('sopenid','oMt59uE55lLOV2KS6vYZ_d0dOl5c')
        unionid = content.get('sunionid','o29cQs9QlfWpL0v0ZV_b2nyTOM-4')
        return (openid, unionid)
    if not code and not request:
        return ('','')
    if not code and request:
        return get_cookie_openid(request.COOKIES, appid)
    
    url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code'
    get_openid_url = url % (appid, secret, code)
    r = urllib.urlopen(get_openid_url).read()
    r = json.loads(r)
    
    if r.has_key("errcode"):
        return ('','')

    return (r.get('openid'),r.get('unionid'))