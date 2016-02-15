# coding:utf-8
__author__ = 'imeron'
import re
import json
import urllib
import urllib2
from django.conf import settings

from . import exceptions
from . import signals

WEIXIN_SNS_USERINFO_URI = '{0}/sns/userinfo?access_token={1}&openid={2}&lang=zh_CN'
WEIXIN_SNS_BASEINFO_URI = '{0}/sns/oauth2/access_token?appid={1}&secret={2}&code={3}&grant_type=authorization_code'

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

def get_weixin_userbaseinfo(code, appid, secret):
    """ 根据code获取用户openid信息 """
    userinfo_url = WEIXIN_SNS_BASEINFO_URI.format(
        settings.WEIXIN_API_HOST,
        appid,
        secret,
        code
    )
    req = urllib2.urlopen(userinfo_url)
    resp = req.read()
    return json.loads(resp)

def get_weixin_snsuserinfo(openid, access_token):
    """ 根据access_token获取用户昵称头像信息 """
    userinfo_url = WEIXIN_SNS_USERINFO_URI.format(
        settings.WEIXIN_API_HOST,
        access_token,
        openid
    )
    req = urllib2.urlopen(userinfo_url)
    resp = req.read()
    return json.loads(resp)

def get_user_unionid(code, 
                    appid='', 
                    secret='',
                    request=None):
    """ 根据code获取用户openid,unoinid,或access_token """
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
    
    r = get_weixin_userbaseinfo(code, appid, secret)
    if r.has_key("errcode"):
        return ('','')
    
    openid = r.get('openid')
    if not r.has_key('unionid') and r.has_key('access_token'):
        r = get_weixin_snsuserinfo(openid, r.get('access_token'))
        if r.has_key("errcode"):
            return (openid,'')
        signals.signal_weixin_snsauth_response.send(sender="access_token",resp_data=r)
        
    return (r.get('openid'),r.get('unionid'))

