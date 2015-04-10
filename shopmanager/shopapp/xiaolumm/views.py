# Create your views here.

import json
from django.http import HttpResponse
from django.shortcuts import redirect

from shopapp.weixin.views import get_user_openid,valid_openid
from models import Clicks


SHOPURL = "http://mp.weixin.qq.com/bizmall/mallshelf?id=&t=mall/list&biz=MzA5NTI1NjYyNg==&shelf_id=2&showwxpaytitle=1#wechat_redirect"


def logclicks(request, linkid):
    content = request.REQUEST
    code = content.get('code',None)

    openid = get_user_openid(request, code)

    if not valid_openid(openid):
        redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://weixin.huyi.so/m/%d/&response_type=code&scope=snsapi_base&state=135#wechat_redirect" % linkid
        return redirect(redirect_url)

    Clicks.objects.create(linkid=linkid,openid=openid)
    
    
    return redirect(SHOPURL)
