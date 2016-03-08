#-*- coding:utf-8 -*-
from django.conf import settings
from django.shortcuts import redirect

from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers 
from rest_framework.response import Response

from core.weixin.mixins import WeixinAuthMixin
from .models import MamaDressResult

class DressUserinfoView(WeixinAuthMixin, APIView):
    
    authentication_classes = ()
    permission_classes = ()
    renderer_classes = (renderers.TemplateHTMLRenderer,)
    template_name = "mmdress/dress_userinfo.html"
        
    def get(self, request, *args, **kwargs):
        
        content = request.REQUEST
        self.set_appid_and_secret(settings.WXPAY_APPID,settings.WXPAY_SECRET)
        user_infos = self.get_auth_userinfo(request)
        unionid = user_infos.get('unionid')
        if not self.valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)
        
        mama_dress,state = MamaDressResult.objects.get_or_create(user_unionid=unionid)
        referal_id = content.get('referal_id',0)
        dresult = MamaDressResult.objects.filter(referal_from=referal_id)
        referal_info = None
        if dresult.exists():
            referal_info = dresult[0]
        
        response = {'user_info':user_infos,
                    'mama_dress':mama_dress,
                    'referal_dress':referal_info,
                    'age_range':range(1976,2001)}
        return Response(response)
    
    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        user_unionid = content.get('user_unionid')
        mm_dress,state = MamaDressResult.objects.get_or_create(user_unionid=user_unionid)
        for k,v in content.iteritems():
            if hasattr(mm_dress, k):
                setattr(mm_dress,k,v)
        mm_dress.save()
        return redirect('./')
        