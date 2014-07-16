#-*- encoding:utf-8 -*-
import re
import time
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from shopapp.weixin.service import WeixinUserService
from models import WeiXinUser,ReferalRelationship,ReferalSummary

import logging
import json

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
        
        content    = request.REQUEST

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


from django.db.models import F

class WeixinAddReferalView(View):
    "add a referal"
    
    def post(self, request):
        content = request.REQUEST
        
        referal_to_mobile = content.get("mobile")
        referal_from_openid = content.get("openid")

        ## check whether referal_to_mobile exists
        if WeiXinUser.objects.filter(mobile=referal_to_mobile).count() > 0 or \
                ReferalRelationship.objects.filter(referal_to_mobile=referal_to_mobile).count() > 0:
            response = {"code":"dup", "message":"referal already exists"}
            return HttpResponse(json.dumps(response),mimetype='application/json')
            
        ## add to referal relationship database
        ReferalRelationship.objects.create(referal_from_openid=referal_from_openid,referal_to_mobile=referal_to_mobile)
        
        ## update referal summary
        obj, created = ReferalSummary.objects.get_or_create(user_openid=referal_from_openid)
        obj.direct_referal_count += 1
        obj.save()

        ## should also update indirect referal summary
        referal_from_user = WeiXinUser.objects.get(openid=referal_from_openid)
        parent_openid = referal_from_user.referal_from_openid
        if parent_openid != "":
            ReferalSummary.objects.filter(user_openid=parent_openid).update(indirect_referal_count=F('indirect_referal_count')+1)

        response = {"code":"ok", "message":"referal added successfully"}
        return HttpResponse(json.dumps(response),mimetype='application/json')

    def get(self, request):
        return self.post(request)
        
        
from django.shortcuts import render_to_response
from django.template import RequestContext
from urllib import urlopen

class ReferalView(View):
    
    def get_user_openid(self, code, appid, secret):
        url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code' % (appid, secret, code)
        r = urlopen(url).read()
        r = json.loads(r)
        return r.get('openid')
        

    def get(self, request):
        content = request.REQUEST

        code = content.get('code')

        APPID = 'wxc2848fa1e1aa94b5'
        SECRET = 'eb3bfe8e9a36a61176fa5cafe341c81f'
        
        user_openid = self.get_user_openid(code, APPID, SECRET)

        direct_referal_count = 0
        referal_bonus = 0.00
        
        rs = ReferalSummary.objects.filter(user_openid=user_openid)
        if rs.count() > 0:
            direct_referal_count = rs[0].direct_referal_count
            referal_bonus = rs[0].total_confirmed_value * 0.01
        
        
        return render_to_response('weixin/referal.html', 
                                  {'openid':user_openid, 'referal_count':direct_referal_count, 'referal_bonus':referal_bonus}, 
                                  context_instance=RequestContext(request))
