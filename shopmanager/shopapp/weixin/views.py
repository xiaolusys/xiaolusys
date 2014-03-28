#-*- encoding:utf8 -*-
import re
import random
import time
import datetime
from lxml import etree
from xml.dom import minidom 
from django.http import HttpResponse
from django.conf import settings
from django.views.generic import View
from shopapp.weixin.models import WeiXinAccount,WeiXinAutoResponse,WeiXinUser,\
    WX_TEXT,WX_IMAGE,WX_VOICE,WX_VIDEO,WX_LOCATION,WX_LINK
from .weixin_apis import WeiXinAPI
from common.utils import parse_datetime
import logging

logger = logging.getLogger('django.request')
VALID_PHONE_REGEX = '^vm:(?P<mobile>1[3458][0-9]{9})$'
VALID_CODE_REGEX    = '^vc:(?P<code>[0-9]{6})$'

class WeixinAcceptView(View):
    """ 微信接收消息接口 """

    _wx_api = WeiXinAPI()
    
    def get(self, request):
        
        content    = request.REQUEST
        wx_account = WeiXinAccount.getAccountInstance()
        
        if wx_account.checkSignature(content['signature'],
                                     content['timestamp'],
                                     content['nonce']):
            wx_account.is_active = True
            wx_account.save()
            
            return HttpResponse(content['echostr'])
        
        return HttpResponse('fails')
    
    
    def parseXML2Param(self,xmlc):
        
        doc     = etree.fromstring(xmlc)
        createtime_stamp = int(doc.xpath('/xml/CreateTime')[0].text)
        msgtype = doc.xpath('/xml/MsgType')[0].text
        
        xmld   = {  'FromUserName':doc.xpath('/xml/FromUserName')[0].text,
                    'ToUserName':doc.xpath('/xml/ToUserName')[0].text,
                    'CreateTime':datetime.datetime.fromtimestamp(createtime_stamp),
                    'MsgType':msgtype,
                    'MsgId':doc.xpath('/xml/MsgId')[0].text
                 }
        if msgtype ==  WX_TEXT: 
            xmld.update(Content=doc.xpath('/xml/Content')[0].text)
        elif msgtype == WX_IMAGE:
            xmld.update(MediaId=doc.xpath('/xml/MediaId')[0].text)
        elif msgtype == WX_VOICE:
            xmld.update(MediaId=doc.xpath('/xml/MediaId')[0].text)
        elif msgtype == WX_VIDEO:
            xmld.update(MediaId=doc.xpath('/xml/MediaId')[0].text)
            
        return xmld
    
    def buildDomByJson(self,parentDom,djson,arrayTag='',rootTag=''):
        
        pdom = parentDom
        doc  = parentDom.ownerDocument or parentDom
        if rootTag:
            pdom = doc.createElement(rootTag)
            parentDom.appendChild(pdom)
            
        json_type = type(djson)
        if json_type == dict:
            
            for k,v in djson.iteritems():
                
                if type(v) in (list,tuple):
                    self.buildDomByJson(pdom,v,arrayTag=k)
                else:
                    dict_dom = doc.createElement(k)
                    pdom.appendChild(dict_dom)
                    self.buildDomByJson(dict_dom,v)                
            return
            
        if json_type in (list,tuple):
            
            if not arrayTag:
                raise Exception(u'数组类型需要指定父标签')
            
            for ajson in djson:
                self.buildDomByJson(pdom,ajson,rootTag=arrayTag)
            return 
        
        if json_type in (str,unicode):
            
            pdom.appendChild(doc.createCDATASection(djson))
            return 
        
        if json_type in (int,float):
            
            pdom.appendChild(doc.createTextNode(str(djson)))
            return
        
        
    
    def formatParam2XML(self,params):  
        """ <xml>
            <ToUserName><![CDATA[oMt59uJJBoNRC7Fdv1b5XiOAngdU]]></ToUserName>
            <FromUserName><![CDATA[gh_4f2563ee6e9b]]></FromUserName>
            <CreateTime>1393562180</CreateTime>
            <MsgType><![CDATA[text]]></MsgType>
            <Content><![CDATA[宝贝好可爱！]]></Content>
            </xml>
        """      
        dom = minidom.Document()
        initStr = dom.toxml()
        
        self.buildDomByJson(dom, params ,rootTag='xml')
        
        return dom.toxml()[len(initStr):]
    
    def getResponseList(self):
        
        return WeiXinAutoResponse.objects.extra(select={'length':'Length(message)'}).order_by('-length')
    
    def reValidMobile(self,msg):
        
        m = re.complile(VALID_PHONE_REGEX).match(msg)
        return m.groupdict().get('mobile')
        
    def reValidCode(self,msg):
         
        m = re.complile(VALID_CODE_REGEX).match(msg)
        return m.groupdict().get('code')
    
    def getOrCreateUser(self,openId):
        
        wx_user,state =  WeiXinUser.objects.get_or_create(openid=openId)       
        if not wx_user.nickname:
            userinfo = self. _wx_api.getUserInfo(openId)
           
            for k,v in userinfo.iteritems():
                setattr(wx_user,k,v)
                
            wx_user.subscribe_time = parse_datetime(userinfo.get('subscribe_time'))
            wx_user.save()
        return wx_user
        
    def genValidCode(self):
        return str( random.randint(100000,999999))
        
    def getValidCode(self,mobile,openId):
        
        wx_user   = self.getOrCreateUser(openId)
        
        if not  wx_user.is_code_time_safe():      
            raise Exception(u'请%d秒后重新发送'%(wx_user.get_wait_time()))
        
        validCode = self.genValidCode()
        self._wx_api.sendValidCode(mobile,validCode)        
        
        wx_user.mobile = mobile
        wx_user.isvalid  = False
        wx_user.validcode = validCode
        wx_user.valid_count += 1
        wx_user.code_time = datetime.datetime.now()
        wx_user.save()
        return validCode
    
    def checkValidCode(self,validCode,openId):
        
         wx_user   = self.getOrCreateUser(openId)
         if wx_user.isvalid:
            return True
             
         if not wx_user.validcode or wx_user.validcode != validCode:
             raise Exception(u'验证码不对，请重新输入，或者重新输发送')
             
         wx_user.isvalid = True
         wx_user.save()
         return True
    
    def getResponseByBestMatch(self,message,*args,**kwargs):
        
        mobile = self.reValidMobile(message)
        if mobile and self.getValidCode(mobile):
            return WeiXinAutoResponse.objects.get_or_create(message=u'校验码提醒')
        
        validCode = self.reValidCode(message)
        if validCode and self.checkValidCode(validCode):
            return WeiXinAutoResponse.objects.get_or_create(message=u'校验成功提示')            
            
        for resp in self.getResponseList():
            if message.rfind(resp.message.strip()) > -1:
                return resp
        return WeiXinAutoResponse.respDefault()
    
    def handleRequest(self,params):
        
        ret_params = {'ToUserName':params['FromUserName'],
                      'FromUserName':params['ToUserName'],
                      'CreateTime':int(time.time())}
        msgtype  = params['MsgType']
        
        matchMsg = ''
        if msgtype == WX_TEXT: 
            matchMsg = params['Content']
        elif msgtype == WX_IMAGE:
            matchMsg = '图片'.decode('utf8')
        elif msgtype == WX_VOICE:
            matchMsg = '语音'.decode('utf8')
        elif msgtype == WX_VIDEO:
            matchMsg = '视频'.decode('utf8')
        elif msgtype == WX_LOCATION:
            matchMsg = '位置'.decode('utf8')
        else:
            matchMsg = '链接'.decode('utf8')
        try:
            resp = self.getResponseByBestMatch(matchMsg.strip(),params)
            ret_params.update(resp.autoParams())
        except Exception,exc:
            ret_params.update(self._wx_api.genTextRespJson(exc.message))
            
        return ret_params
        
    def post(self,request):
        
        content    = request.GET
        wx_account = WeiXinAccount.getAccountInstance()
        
        if not wx_account.checkSignature(content['signature'],
                                     content['timestamp'],
                                     content['nonce']):
            return HttpResponse('INVALID MESSAGE')
        
        content  = request.body
        
        params   = self.parseXML2Param(content)
        
        ret_params = self.handleRequest(params)
       
        response = self.formatParam2XML(ret_params)
        
        return HttpResponse(response,mimetype="text/xml")

        

        
        
        
