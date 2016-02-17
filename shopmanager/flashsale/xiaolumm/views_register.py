#-*- coding:utf-8 -*-

import json
import datetime
import urllib
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse,Http404
from django.shortcuts import redirect,render_to_response,get_object_or_404
from django.views.generic import View
from django.template import RequestContext
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers 
from rest_framework.response import Response

from core.weixin.mixins import WeixinAuthMixin

from flashsale.pay.options import get_user_unionid,valid_openid
from flashsale.pay.mixins import PayInfoMethodMixin
from flashsale.xiaolumm.models import XiaoluMama
from shopapp.weixin.models import WeiXinUser
from shopback.items.models import Product

import logging
logger = logging.getLogger('django.request')

class MamaRegisterView(WeixinAuthMixin,APIView):
    
#     authentication_classes = (authentication.TokenAuthentication,)
#     permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "apply/mama_profile.html"
    
    def get_deposite_product(self):
        return Product.objects.get(id=2731)
    
    
    def get(self, request, mama_id):
        openid,unionid = self.get_openid_and_unionid(request)
        if not valid_openid(openid) or not valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)
        
        wx_user,state = WeiXinUser.objects.get_or_create(openid=openid)
        try:
            xiaolumm = XiaoluMama.objects.get(openid=unionid)
        except XiaoluMama.DoesNotExist: 
            xiaolumm = None
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
            raise exc
        
        if xiaolumm.progress == XiaoluMama.PASS:
            return redirect(reverse('mama_homepage'))
        
        if xiaolumm.progress == XiaoluMama.PROFILE:
            self.template_name = 'apply/mama_deposit.html'
            product = self.get_deposite_product()
            return Response({'wxuser':wx_user,'xlmm':xiaolumm,'product':product})
            
        elif xiaolumm.progress == XiaoluMama.PAY:
            self.template_name = 'apply/mama_contact.html'
            try:
                referal_mama = XiaoluMama.objects.get(mobile=xiaolumm.referal_from)
                username = User.objects.get(id=referal_mama.manager).username
            except (XiaoluMama.DoesNotExist, User.DoesNotExist):
                username = ''
            return Response({'wxuser':wx_user,'xlmm':xiaolumm})
            
            
    def post(self,request, mama_id):
        content = request.REQUEST
        openid  = content.get('openid')
        unionid = content.get('unionid')
#         nickname  = content.get('nickname')

        wx_user = get_object_or_404(WeiXinUser,openid=openid)
        if not wx_user.isValid() or not valid_openid(unionid):#or not nickname
            return redirect('./')
        
        xlmm, state = XiaoluMama.objects.get_or_create(openid=unionid)
        parent_mobile = xlmm.referal_from
        if int(mama_id) > 0 and not parent_mobile:
            parent_xlmm = get_object_or_404(XiaoluMama,id=mama_id)
            parent_mobile = parent_xlmm.mobile
            
        xlmm.progress = XiaoluMama.PROFILE
        xlmm.referal_from = parent_mobile
        xlmm.save()
        
        return render_to_response("mama_deposit.html", 
                                  {'wxuser':wx_user,'xlmm':xlmm},
                                  context_instance=RequestContext(request))
        
class PayDepositeView(PayInfoMethodMixin, APIView):
    
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer,)
    
    def post(self,request):
        content = request.REQUEST
        openid  = content.get('openid')
        unionid = content.get('unionid')
        
        wx_user = get_object_or_404(WeiXinUser,openid=openid)
        if not wx_user.isValid():
            return redirect('./')
        
        xlmm = get_object_or_404(XiaoluMama,openid=unionid,progress=XiaoluMama.PAY)
        xlmm.progress = XiaoluMama.PASS
        xlmm.save()
        
        return Response({})
        
        
class MamaConfirmView(APIView):
    
#     authentication_classes = (authentication.TokenAuthentication,)
#     permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer,renderers.TemplateHTMLRenderer)
    template_name = "apply/mama_profile.html"
        
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
    
     
