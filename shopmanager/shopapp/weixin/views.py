#-*- encoding:utf8 -*-
import json
import time
import datetime
import urllib,urllib2
from lxml import etree
from xml.dom import minidom 
from StringIO import StringIO
from django.http import HttpResponse
from django.conf import settings
from django.views.generic import View
from shopapp.weixin.models import WeiXinAccount,WeiXinAutoResponse,WeiXinUser,\
    WX_TEXT,WX_IMAGE,WX_VOICE,WX_VIDEO,WX_LOCATION,WX_LINK
from common.xmlutils import makeEasyTag
import logging

logger = logging.getLogger('django.request')


class WeixinAcceptView(View):
    """ 微信接收消息接口 """
    
    
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
    
    def getResponseByBestMatch(self,message):
        
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
        
        resp = self.getResponseByBestMatch(matchMsg.strip())
        ret_params.update(resp.autoParams())
        
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

        
class WeixinMobileValidView(View):
    
    def get(self,request):
        
        pass
        
    def post(self,request):
    
        pass
        
        
        
