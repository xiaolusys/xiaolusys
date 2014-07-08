#-*- encoding:utf8 -*-
import re
import time
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from shopapp.weixin.service import WeixinUserService
import logging

logger = logging.getLogger('django.request')

@csrf_exempt
def wxpay(request):
    logger.error('WEIXIN WEIXIN_PAY_URL:%s'%str(request.REQUEST))
    return HttpResponse('success')

@csrf_exempt
def napay(request):
    logger.error('WEIXIN NATIVE_CALLBACK_URL:%s'%str(request.REQUEST))
    return HttpResponse('success')

@csrf_exempt
def rights(request):
    logger.error('WEIXIN FEEDBACK_URL:%s'%str(request.REQUEST))
    return HttpResponse('success')

@csrf_exempt
def warn(request):
    logger.error('WEIXIN WARN_URL:%s'%str(request.REQUEST))
    return HttpResponse('success')


class WeixinAcceptView(View):
    """ 微信接收消息接口 """
    
    def get_wx_service(self):
       return WeixinUserService()
    
    def get(self, request):
        
        content    = request.REQUEST
        
        wx_service = self.get_wx_service()
        if wx_service.checkSignature(content.get('signature',''),
                                     content.get('timestamp',0),
                                     content.get('nonce','')):
            wx_service.activeAccount()
            
            return HttpResponse(content['echostr'])
        
        return HttpResponse(u'微信接口验证失败')
    
    
    def post(self,request):
        
        content    = request.GET
        
        wx_service = self.get_wx_service()
        if not wx_service.checkSignature(content.get('signature',''),
                                         content.get('timestamp',0),
                                         content.get('nonce','')):
            return HttpResponse(u'非法请求')
        
        content  = request.body
        
        params   = wx_service.parseXML2Param(content)
        
        ret_params = wx_service.handleRequest(params)
       
        response = wx_service.formatParam2XML(ret_params)
        
        return HttpResponse(response,mimetype="text/xml")

        

        
        
        
