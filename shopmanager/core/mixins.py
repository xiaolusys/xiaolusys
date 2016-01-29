import json
import urllib
from django.conf import settings
import re
OPENID_RE = re.compile('^[a-zA-Z0-9-_]{28}$')


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


class WeixinAuthMixin(object):

    def valid_openid(self, openid):
        if not openid:
            return False
        if not OPENID_RE.match(openid):
            return False
        return True

    def get_openid_and_unionid(self, request):
        code    = request.GET.get('code')
        return get_user_unionid(
            code,
            appid=settings.WEIXIN_APPID,
            secret=settings.WEIXIN_SECRET,
            request=request
        )
    
    def get_wxauth_redirct_url(self,request):
        absolute_url = request.build_absolute_uri().split('#')[0]
        params = {'appid':settings.WEIXIN_APPID,
                  'redirect_uri':absolute_url,
                  'response_type':'code',
                  'scope':'snsapi_base',
                  'state':'135'}
        redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?{0}"
        return redirect_url.format(urllib.urlencode(params))
    
    