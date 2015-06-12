#-*- coding:utf-8 -*-

import json
import datetime
import urllib
from django.http import HttpResponse,Http404
from django.shortcuts import redirect,render_to_response,get_object_or_404
from django.views.generic import View
from django.template import RequestContext
from django.contrib.auth.models import User
from django.db import models
from django.conf import settings

from django.core.urlresolvers import reverse
from flashsale.pay.options import get_user_unionid,valid_openid
from flashsale.xiaolumm.models import XiaoluMama
from shopapp.weixin.models import WeiXinUser
from flashsale.xiaolumm import xlmm_kefukeys as kfkeys

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
            params = {'appid':settings.WEIXIN_APPID,
                      'redirect_uri':request.build_absolute_uri().split('#')[0],
                      'response_type':'code',
                      'scope':'snsapi_base',
                      'state':'135'}
            redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?{0}"
            return redirect(redirect_url.format(urllib.urlencode(params)))
        
        wx_user,state = WeiXinUser.objects.get_or_create(openid=openid)
        kf_url = ''
        try:
            xiaolumm = XiaoluMama.objects.get(openid=unionid)
            if xiaolumm.progress == XiaoluMama.PASS:
                return redirect(reverse('mama_homepage'))
            
            if xiaolumm.progress == XiaoluMama.PROFILE:
                self.template_name = 'mama_deposit.html'
            elif xiaolumm.progress == XiaoluMama.PAY:
                self.template_name = 'mama_contact.html'
                
                try:
                    referal_mama = XiaoluMama.objects.get(mobile=xiaolumm.referal_from)
                    username = User.objects.get(id=referal_mama.manager).username
                except (XiaoluMama.DoesNotExist,User.DoesNotExist):
                    username = ''
                    
                kf_name = kfkeys.NAME_KEY_MAP.get(username,None)
                if not kf_name:
                    rindex = xiaolumm.id % len(kfkeys.KEY_LIST)
                    kf_key = kfkeys.KEY_LIST[rindex] - 1
                    kf_name = kfkeys.KEY_MAP[kf_key]
                
                kf_url = '%s%s'%(kfkeys.IMG_URL_PREFIX,kfkeys.KEY_URLS_MAP.get(kf_name))
            
        except XiaoluMama.DoesNotExist: 
            xiaolumm = None
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            raise exc
        
        return Response({'wxuser':wx_user,'xlmm':xiaolumm,'kefu_url':kf_url})
        
    def post(self,request, mama_id):
        content = request.REQUEST
        openid  = content.get('openid')
        unionid = content.get('unionid')
#         nickname  = content.get('nickname')

        wx_user = get_object_or_404(WeiXinUser,openid=openid)
        
        if not wx_user.isValid() or not valid_openid(unionid) :#or not nickname
            return redirect('./')
        
        parent_mobile = ''
        if int(mama_id) > 0:
            parent_xlmm = get_object_or_404(XiaoluMama,id=mama_id)
            parent_mobile = parent_xlmm.mobile
            
        xlmm, state = XiaoluMama.objects.get_or_create(openid=unionid)
#         xlmm.weikefu = nickname
        xlmm.progress = XiaoluMama.PROFILE
        xlmm.referal_from = parent_mobile
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
    
     
