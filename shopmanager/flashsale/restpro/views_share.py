# -*- coding:utf8 -*-
import urllib 
import datetime
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.conf import settings

from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import status
from rest_framework import exceptions

from flashsale.pay.models import CustomShare,Customer
from flashsale.xiaolumm.models import XiaoluMama

from shopapp.weixin.weixin_apis import WeiXinAPI,WeiXinRequestException
from . import permissions as perms
from . import serializers 
from shopback.base import log_action, ADDITION, CHANGE


class CustomShareViewSet(viewsets.ModelViewSet):
    """
    特卖分享API：
    - {prefix}/today[.format]: 获取今日分享内容;
    """
    queryset = CustomShare.objects.filter(status=True)
    serializer_class = serializers.CustomShareSerializer
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    def get_xlmm(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        if not customer.unionid.strip():
            return None
        xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
        return xiaolumms.count() > 0 and xiaolumms[0] or None
    
    def is_request_from_weixin(self,request):
        user_agent = request.META.get('HTTP_USER_AGENT')
        if user_agent and user_agent.find('MicroMessenger') > 0: 
            return True
        return False
    
    @list_route(methods=['get'])
    def today(self, request, *args, **kwargs):
        """ 获取今日分享链接内容 """
        today = datetime.date.today()
        queryset = self.get_queryset()
        queryset = queryset.filter(active_at__lte=today).order_by('-active_at')
        if queryset.count() == 0 :
            raise exceptions.APIException('not found!')
        
        cshare   = queryset[0]
        serializer = self.get_serializer(cshare, many=False)
        resp     = serializer.data
        
        xlmm     = self.get_xlmm(request)
        xlmm_id  = xlmm and xlmm.id or 0
        share_url = cshare.share_link({'xlmm':xlmm_id})
        resp['share_link'] = share_url
        if self.is_request_from_weixin(request): #
            wx_api     = WeiXinAPI()
            signparams = wx_api.getShareSignParams(share_url)
            resp['wx_singkey'] = signparams

        return Response(resp)
    
