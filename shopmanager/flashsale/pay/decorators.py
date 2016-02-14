#-*- encoding:utf8 -*-
import urllib
from functools import wraps
from django.http import HttpResponseRedirect
from django.utils.decorators import available_attrs
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login as auth_login, SESSION_KEY
from django.conf import settings

from core import options

def sale_buyer_required(view_func):
    """
    Decorator for views that checks that the user is logged in and is a staff
    member, displaying the login page if necessary.
    """
    def _checklogin(request, *args, **kwargs):
        if request.user.is_active :
            # The user is valid. Continue to the admin page.
            return view_func(request, *args, **kwargs)

        code   = request.GET.get('code')
        user_agent = request.META.get('HTTP_USER_AGENT')
        if user_agent and user_agent.find('MicroMessenger') >= 0:
            if not code :
                params = {'appid':settings.WXPAY_APPID,
                          'redirect_uri':request.build_absolute_uri().split('#')[0],
                          'response_type':'code',
                          'scope':'snsapi_base',
                          'state':'135'}
                redirect_url = options.gen_weixin_redirect_url(params)
                return HttpResponseRedirect(redirect_url)
            
            else :
                user = authenticate(request=request)
                if not user or user.is_anonymous():
                    return HttpResponseRedirect(reverse('flashsale_login'))
                    
                request.session[SESSION_KEY] = user.id
                auth_login(request, user)
                
                return view_func(request, *args, **kwargs)
            
        defaults = {
            "title":u'登录',
            REDIRECT_FIELD_NAME: request.build_absolute_uri().split('#')[0]
        }
        return render_to_response("pay/mlogin.html", defaults,
                                  context_instance=RequestContext(request))
        
    return wraps(view_func, assigned=available_attrs(view_func))(_checklogin)

def weixin_xlmm_auth(redirecto=None):
    """
    Decorator for views that checks that the user is logged in and is a staff
    member, displaying the login page if necessary.
    """
    def _decorator(view_func):
        
        assert redirecto ,u'redirecto 参数必须'
        def _checklogin(request, *args, **kwargs):
            if request.user.is_active :
                # The user is valid. Continue to the admin page.
                return view_func(request, *args, **kwargs)
            
            code   = request.GET.get('code')
            user_agent = request.META.get('HTTP_USER_AGENT')
            if not user_agent or user_agent.find('MicroMessenger') < 0:
                return HttpResponseRedirect(redirecto)
            
            if not code :
                params = {'appid':settings.WXPAY_APPID,
                          'redirect_uri':request.build_absolute_uri().split('#')[0],
                          'response_type':'code',
                          'scope':'snsapi_base',
                          'state':'135'}
                redirect_url = options.gen_weixin_redirect_url(params)
                return HttpResponseRedirect(redirect_url)
            
            else :
                user = authenticate(request=request)
                if not user or user.is_anonymous():
                    return HttpResponseRedirect(redirecto)
                    
                auth_login(request, user)
                
                return view_func(request, *args, **kwargs)
        
        return wraps(view_func, assigned=available_attrs(view_func))(_checklogin)
    return _decorator

import logging
logger = logging.getLogger('django.request')

def weixin_test_auth(redirecto=None):
    """
    Decorator for views that checks that the user is logged in and is a staff
    member, displaying the login page if necessary.
    """
    def _decorator(view_func):
        
        assert redirecto ,u'redirecto 参数必须'
        def _checklogin(request, *args, **kwargs):
            if request.user.is_active :
                # The user is valid. Continue to the admin page.
                return view_func(request, *args, **kwargs)
            
            code   = request.GET.get('code')
            user_agent = request.META.get('HTTP_USER_AGENT')
            if not user_agent or user_agent.find('MicroMessenger') < 0:
                return HttpResponseRedirect(redirecto)
            
            if not code :
                params = {'appid':settings.WXPAY_APPID,
                          'redirect_uri':request.build_absolute_uri().split('#')[0],
                          'response_type':'code',
                          'scope':'snsapi_base',
                          'state':'135'}
                redirect_url = options.gen_weixin_redirect_url(params)
                return HttpResponseRedirect(redirect_url)
            
            else :
                user = authenticate(request=request)
                if not user or user.is_anonymous():
                    return HttpResponseRedirect(redirecto)
                
                auth_login(request, user)
                
                return view_func(request, *args, **kwargs)
        
        return wraps(view_func, assigned=available_attrs(view_func))(_checklogin)
    return _decorator

