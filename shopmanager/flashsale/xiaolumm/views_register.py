#-*- coding:utf-8 -*-

import json
import datetime
from django.http import HttpResponse,Http404
from django.shortcuts import redirect,render_to_response,get_object_or_404
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
        
    def get(self, request, mama_id):
        content = request.REQUEST
        code    = content.get('code')
        openid,unionid = get_user_unionid(code,
                                          appid=settings.WEIXIN_APPID,
                                          secret=settings.WEIXIN_SECRET,
                                          request=request)
        
        if not valid_openid(openid) or not valid_openid(unionid):
            register_url = reverse('mama_register')
            redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri={0}&response_type=code&scope=snsapi_base&state=135#wechat_redirect"
            return redirect(redirect_url.format(register_url))
        
        wx_user,state = WeiXinUser.objects.get_or_create(openid=openid)
        
        try:
            xiaolumm = XiaoluMama.objects.get(openid=unionid)
            if xiaolumm.progress == XiaoluMama.PASS:
                return redirect(reverse('mama_homepage'))
            
            if xiaolumm.progress == XiaoluMama.PROFILE:
                self.template_name = 'mama_deposit.html'
            elif xiaolumm.progress == XiaoluMama.PAY:
                self.template_name = 'mama_contact.html'
                
        except XiaoluMama.DoesNotExist: 
            xiaolumm = None
        
        return Response({'wxuser':wx_user,'xlmm':xiaolumm})
        
    def post(self,request, mama_id):
        content = request.REQUEST
        openid  = content.get('openid')
        unionid = content.get('unionid')
        nickname  = content.get('nickname')

        wx_user = get_object_or_404(WeiXinUser,openid=openid)
        
        if not wx_user.isValid() or not valid_openid(unionid) or not nickname:
            return redirect('./')
        
        parent_xlmm = get_object_or_404(XiaoluMama,id=mama_id)
        
        xlmm, state = XiaoluMama.objects.get_or_create(openid=unionid)
        xlmm.weikefu = nickname
        xlmm.progress = XiaoluMama.PROFILE
        xlmm.referal_from = parent_xlmm.mobile
        xlmm.save()
        
        return render_to_response("mama_deposit.html", 
                                  {'wxuser':wx_user,'xlmm':xlmm},
                                  context_instance=RequestContext(request))
        
class MamaConfirmView(APIView):
    
#     authentication_classes = (authentication.TokenAuthentication,)
#     permission_classes = (permissions.IsAuthenticated,)
    template_name = "mama_profile.html"
        
    def post(self,request):
        content = request.REQUEST
        openid  = content.get('openid')
        unionid = content.get('unionid')
        
        wx_user = get_object_or_404(WeiXinUser,openid=openid)
        if not wx_user.isValid() :
            return redirect('./')
        
        xlmm = get_object_or_404(XiaoluMama,openid=unionid,progress=XiaoluMama.PAY)
        xlmm.progress = XiaoluMama.PASS
        xlmm.save()
        
        return redirect(reverse('mama_homepage'))     
    
     
