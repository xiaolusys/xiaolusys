# coding:utf-8
__author__ = 'imeron'
import re
import json
import urllib
from django.conf import settings

from . import exceptions
from . import signals

def gen_weixin_redirect_url(params):
    list_params = ['appid','redirect_uri','response_type','scope','state']
    param_string = '&'.join([urllib.urlencode({t:params.get(t,'')}) for t in list_params])
    redirect_url = "{0}?{1}#wechat_redirect"
    return redirect_url.format(settings.WEIXIN_AUTHORIZE_URL,param_string)

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
    state     = content.get('state',None)
    if not debug_m and request: 
        debug_m = content.get('debug')
    if debug_m:
        openid  = content.get('sopenid','oMt59uE55lLOV2KS6vYZ_d0dOl5c')
        unionid = content.get('sunionid','o29cQs9QlfWpL0v0ZV_b2nyTOM-4')
        return (openid, unionid)
    if state and not code:
        raise exceptions.WeixinAutherizeFail('(用户取消授权,%s)'%content)
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
    
    signals.signal_weixin_snsauth_response.send(sender="access_token",resp_data=r)
    
    return (r.get('openid'),r.get('unionid'))

