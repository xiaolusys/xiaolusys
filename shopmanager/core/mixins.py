import re
import json
import urllib
from django.conf import settings

from .options import get_user_unionid

OPENID_RE = re.compile('^[a-zA-Z0-9-_]{28}$')

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
    
    