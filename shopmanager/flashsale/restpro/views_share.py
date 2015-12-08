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

from . import permissions as perms
from . import serializers 
from shopback.base import log_action, ADDITION, CHANGE


class CustomShareViewSet(viewsets.ReadOnlyModelViewSet):
    """
    特卖分享API：
    - {prefix}/today[.format]: 获取今日分享内容;
    """
    queryset = CustomShare.objects.filter(status=True)
    serializer_class = serializers.CustomShareSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    renderer_classes = (renderers.JSONRenderer,renderers.BrowsableAPIRenderer,)
    
    def get_xlmm(self,request):
        customer = get_object_or_404(Customer,user=request.user)
        if not customer.unionid.strip():
            return None
        xiaolumms = XiaoluMama.objects.filter(openid=customer.unionid)
        return xiaolumms.count() > 0 and xiaolumms[0] or None
    
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
        resp['share_link'] = cshare.share_link({'xlmm':xlmm_id})
        return Response(resp)
    
    @list_route(methods=['get'])
    def weixin(self, request, *args, **kwargs):
        """ 获取微信分享参数 """
        xlmm   = self.get_xlmm(request)
        code   = request.GET.get('code')
        user_agent = request.META.get('HTTP_USER_AGENT')
        if not xlmm and user_agent and user_agent.find('MicroMessenger') > 0:
            if not code :
                params = {'appid':settings.WXPAY_APPID,
                          'redirect_uri':request.build_absolute_uri().split('#')[0],
                          'response_type':'code',
                          'scope':'snsapi_base',
                          'state':'135'}
                redirect_url = ('{0}?{1}').format(settings.WEIXIN_AUTHORIZE_URL,urllib.urlencode(params))
                return HttpResponseRedirect(redirect_url)
            else:
                pass
        
        today = datetime.date.today()
        queryset = self.get_queryset()
        queryset = queryset.filter(active_at__lte=today).order_by('-active_at')
        if queryset.count() == 0 :
            raise exceptions.APIException('not found!')
        
        cshare   = queryset[0]
        serializer = self.get_serializer(cshare, many=False)
        resp     = serializer.data
        
        xlmm_id  = xlmm and xlmm.id or 0
        resp['share_link'] = cshare.share_link({'xlmm':xlmm_id})
        return Response(resp)
