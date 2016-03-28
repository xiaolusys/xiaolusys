#-*- encoding:utf8 -*-
from functools import wraps
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login as auth_login
from django.conf import settings

from . import options
from . import constants
import logging
logger = logging.getLogger('django.request')


def weixin_authlogin_required(redirecto=None):
    """
    Decorator for views that checks that the user is logged in and is a staff
    member, displaying the login page if necessary.
    """
    def _decorator(view_func):
        assert redirecto ,u'redirecto 参数必须'
        @wraps(view_func)
        def _checklogin(request, *args, **kwargs):
            if request.user.is_active:
                # The user is valid. Continue to the admin page.
                return view_func(request, *args, **kwargs)
            
            code   = request.GET.get('code')
            user_agent = request.META.get('HTTP_USER_AGENT')
            if not user_agent or user_agent.lower().find('micromessenger') < 0:
                return HttpResponseRedirect(redirecto)
            
            if not code:
                openid, unionid = options.get_cookie_openid(request.COOKIES, settings.WXPAY_APPID)
                if not options.valid_openid(unionid):
                    params = {'appid':settings.WXPAY_APPID,
                      'redirect_uri':request.build_absolute_uri().split('#')[0],
                      'response_type':'code',
                      'scope':'snsapi_userinfo',
                      'state':'135'}
                    redirect_url = options.gen_weixin_redirect_url(params)
                    logger.info('weixin redirect:redirect_url=%s'%(redirect_url))
                    return redirect(redirect_url)
            logger.info('weixin authenticate:%s,%s'%(code,user_agent))
            user = authenticate(request=request, handle_backends=[constants.WEIXIN_AUTHENTICATE_KEY])
            if not user or user.is_anonymous():
                return HttpResponseRedirect(redirecto)
            logger.info('weixin authlogin:%s,%s'%(code,user))
            auth_login(request, user)
            return view_func(request, *args, **kwargs)
        
        return _checklogin
    return _decorator
