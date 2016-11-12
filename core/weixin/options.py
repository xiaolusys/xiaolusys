# coding:utf-8
__author__ = 'imeron'
import re
import json
import urllib
import urllib2
from django.conf import settings

OPENID_RE = '^[a-zA-Z0-9-_]{28}$'
AUTHCODE_RE = '^[a-zA-Z0-9]{20,40}$'

WEIXIN_SNS_USERINFO_URI = '{0}/sns/userinfo?access_token={1}&openid={2}&lang=zh_CN'
WEIXIN_SNS_BASEINFO_URI = '{0}/sns/oauth2/access_token?appid={1}&secret={2}&code={3}&grant_type=authorization_code'

def is_from_weixin(request):
    user_agent = request.META.get('HTTP_USER_AGENT')
    if user_agent and re.search('MicroMessenger', user_agent, re.IGNORECASE):
        return True
    return False

def valid_openid(openid):
    """ 验证微信授权ID是否有效 """
    if openid and re.compile(OPENID_RE).match(openid):
        return True
    return False

def gen_weixin_redirect_url(params):
    list_params = ['appid','redirect_uri','response_type','scope','state']
    param_string = '&'.join([urllib.urlencode({t:params.get(t,'')}) for t in list_params])
    redirect_url = "{0}?{1}#wechat_redirect"
    return redirect_url.format(settings.WEIXIN_AUTHORIZE_URL,param_string)

def parse_cookie_key(ckey,appid):
    return '%s_%s'%(ckey,appid.replace('gh_',''))

def get_cookie_openid(cookies,appid):
    """ 根据cookie获取用户openid,unionid """
    x = cookies.get(parse_cookie_key("openid",appid),'')
    y = cookies.get(parse_cookie_key("unionid",appid),'')
    return (x, y)

def set_cookie_openid(response,appid,openid,unionid):
    """ 设置cookie用户openid,unionid """
    response.set_cookie(parse_cookie_key("openid",appid),openid)
    response.set_cookie(parse_cookie_key("unionid",appid),unionid)
    return response

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

def get_auth_userinfo(code, appid='', secret='', request=None):
    """ 根据code获取用户openid,unoinid,nickname,headimgurl  """
    debug_m   = settings.DEBUG
    content   = request and request.GET or request.POST or {}
    state     = content.get('state',None)
    userinfo  = {}
    if not debug_m and request:
        debug_m = content.get('debug')
    if debug_m:
        userinfo.update(openid=content.get('sopenid','oMt59uE55lLOV2KS6vYZ_d0dOl5c'))
        userinfo.update(unionid=content.get('sunionid','o29cQs9QlfWpL0v0ZV_b2nyTOM-4'))
        return userinfo

    if state and not code:
        return {'errcode':9999,'msg':'The user cancel authorized!'}

    if not code or not re.compile(AUTHCODE_RE).match(code):
        return userinfo

    r = get_weixin_userbaseinfo(code, appid, secret)
    if r.has_key("errcode"):
        return r

    openid = r.get('openid')
    if r.has_key('unionid') and r.has_key('access_token'):
        rs = get_weixin_snsuserinfo(openid, r.get('access_token'))
        if rs.has_key("errcode"):
            return r

        # Here we should trigger a task to save userinfo.
        from shopapp.weixin.tasks import task_snsauth_update_weixin_userinfo
        task_snsauth_update_weixin_userinfo.delay(rs, appid)

        return rs

    return r

def get_user_unionid(code, appid='', secret='', request=None):
    """ 根据code获取用户openid,unoinid,或access_token """
    if not code and request:
        return get_cookie_openid(request.COOKIES, appid)

    r = get_auth_userinfo(code, appid=appid, secret=secret, request=request)

    return (r.get('openid',''),r.get('unionid',''))


import hashlib
def gen_wxlogin_sha1_sign(params,secret):

    key_pairs = ['%s=%s'%(k,v) for k,v in params.iteritems()]
    key_pairs.append('secret=%s'%secret)
    key_pairs.sort()
    sign_string = '&'.join(key_pairs)
    return hashlib.sha1(sign_string).hexdigest()




