#-*- coding:utf-8 -*-

import json
import datetime
from django.http import HttpResponse,Http404
from django.shortcuts import redirect,render_to_response
from django.views.generic import View
from django.template import RequestContext
from django.contrib.auth.models import User
from django.db.models import Sum
from django.conf import settings

from django.core.urlresolvers import reverse
from flashsale.pay.options import get_user_unionid,valid_openid
from flashsale.xiaolumm.models import XiaoluMama
from shopapp.weixin.models import WeiXinUser
from .models import Clicks, XiaoluMama

from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import permissions
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


import logging
logger = logging.getLogger('django.request')

class MamaRegisterView(APIView):
    
#     authentication_classes = (authentication.TokenAuthentication,)
#     permission_classes = (permissions.IsAuthenticated,)
    template_name = "mama_profile.html"
        
    def get(self,request):
        content = request.REQUEST
        code    = content.get('code')
        openid,unionid = get_user_unionid(code,
                                          appid=settings.WEIXIN_APPID,
                                          secret=settings.WEIXIN_SECRET,
                                          request=request)
        
        if not valid_openid(openid) or not valid_openid(openid):
            register_url = reverse('mama_register')
            redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri={0}&response_type=code&scope=snsapi_base&state=135#wechat_redirect"
            return redirect(redirect_url.format(register_url))
        
        wx_user,state = WeiXinUser.objects.get_or_create(openid=openid,unionid=unionid)
        
        xiaolumm,state = XiaoluMama.objects.get_or_create(openid=unionid)
        
        return Response({'wxuser':wx_user,'xiaolumm':xiaolumm})
        
    def post(self,request):
        content = request.REQUEST
        return render_to_response("stats.html", 
                                  {'pk':1},
                                  context_instance=RequestContext(request))
        
        
        