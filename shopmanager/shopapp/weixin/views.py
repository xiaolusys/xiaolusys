#-*- encoding:utf8 -*-
import re
import time
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.views.generic import View
from shopapp.weixin.service import WeixinUserService
import logging

logger = logging.getLogger('django.request')

def wxpay(request):
    return HttpResponse('OK')

def napay(request):
    return HttpResponse('OK')

def maintian(request):
    return HttpResponse('OK')

def warn(request):
    print 'WEIXIN WARN:',request.REQUEST
    return HttpResponse('OK')


class WeixinAcceptView(View):
    """ 微信接收消息接口 """
    
    def get_wx_service(self):
       return WeixinUserService()
    
    def get(self, request):
        
        content    = request.REQUEST
        
        wx_service = self.get_wx_service()
        if wx_service.checkSignature(content['signature'],
                                     content['timestamp'],
                                     content['nonce']):
            wx_service.activeAccount()
            
            return HttpResponse(content['echostr'])
        
        return HttpResponse('fails')
    
    
    def post(self,request):
        
        content    = request.GET
        
        wx_service = self.get_wx_service()
        if not wx_service.checkSignature(content.get('signature',''),
                                     content.get('timestamp',''),
                                     content.get('nonce','')):
            return HttpResponse('INVALID MESSAGE')
        
        content  = request.body
        
        params   = wx_service.parseXML2Param(content)
        
        ret_params = wx_service.handleRequest(params)
       
        response = wx_service.formatParam2XML(ret_params)
        
        return HttpResponse(response,mimetype="text/xml")

        

        
        
        
