#-*- encoding:utf8 -*-
import json
import datetime
import urllib,urllib2
from django.http import HttpResponse
from django.conf import settings
from django.views.generic import View
from shopapp.weixin.models import WeiXinAccount
import logging

logger = logging.getLogger('django.request')

_mp_show_qrcode_url = "https://mp.weixin.qq.com/cgi-bin/showqrcode"

class WeixinAcceptView(View):
    """ 微信接收消息接口 """
    
    
    def get(self, request):
        
        content    = request.REQUEST
        wx_account = WeiXinAccount.getAccountInstance()
        
        if wx_account.checkSignature(
                                     content['signature'],
                                     content['timestamp'],
                                     content['nonce']):
            wx_account.is_active = True
            wx_account.save()
            
            return HttpResponse(content['echostr'])
        
        return HttpResponse('fails')
    
    def post(self,request):
        """
            u'<xml>
                <ToUserName><![CDATA[gh_4f2563ee6e9b]]></ToUserName>
                <FromUserName><![CDATA[oMt59uJJBoNRC7Fdv1b5XiOAngdU]]></FromUserName>
                <CreateTime>1393562178</CreateTime>
                <MsgType><![CDATA[text]]></MsgType>
                <Content><![CDATA[Hello]]></Content>
                <MsgId>5985303979652573971</MsgId>
            </xml>'
        """
        content = request.REQUEST
        
        print 'debug:',content
        
        
        
        return HttpResponse("""<xml>
                            <ToUserName><![CDATA[oMt59uJJBoNRC7Fdv1b5XiOAngdU]]></ToUserName>
                            <FromUserName><![CDATA[gh_4f2563ee6e9b]]></FromUserName>
                            <CreateTime>1393562180</CreateTime>
                            <MsgType><![CDATA[text]]></MsgType>
                            <Content><![CDATA[宝贝好可爱！]]></Content>
                            </xml>""")
#        return HttpResponse(json.dumps({
#            "touser":"oMt59uJJBoNRC7Fdv1b5XiOAngdU",
#            "msgtype":"text",
#            "text":
#            {
#                 "content":u"你真可爱！"
#            }
#        }),mimetype='application/json')
#        
        
        
        
        
        
        
