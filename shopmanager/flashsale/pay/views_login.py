#-*- encoding:utf8 -*-
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth import authenticate, login as auth_login, SESSION_KEY

import logging
logger = logging.getLogger('django.request')

def flashsale_login(request):
    
    next_url = request.REQUEST.get(REDIRECT_FIELD_NAME,reverse('sale_home'))
    if request.method == 'GET':
        
        defaults = {
            "title":u'登录',
            REDIRECT_FIELD_NAME: next_url
        }
        return render_to_response("pay/mlogin.html", defaults,
                                  context_instance=RequestContext(request))
    else:
        req_params = request.POST
        user = authenticate(request=request,**req_params)
        if not user or user.is_anonymous():
            
            defaults = {
                "title":u'登录',
                REDIRECT_FIELD_NAME: next_url
            }
            return render_to_response("pay/mlogin.html", defaults,
                                      context_instance=RequestContext(request))
    
        
        request.session[SESSION_KEY] = user.id
        auth_login(request, user)
    
        return HttpResponseRedirect(next_url)

import urllib

def weixin_login(request):
    code   = request.GET.get('code')
    if not code :
        params = {'appid':settings.WXPAY_APPID,
                  'redirect_uri':request.build_absolute_uri().split('#')[0],
                  'response_type':'code',
                  'scope':'snsapi_base',
                  'state':'135'}
        redirect_url = ('{0}?{1}').format(settings.WEIXIN_AUTHORIZE_URL,urllib.urlencode(params))
        return HttpResponseRedirect(redirect_url)
    else :
        user = authenticate(request=request)
        if not user or user.is_anonymous():
            return HttpResponseRedirect('/denglu.html')
        
        request.session[SESSION_KEY] = user.id
        auth_login(request, user)
        
        return HttpResponseRedirect('/')




    