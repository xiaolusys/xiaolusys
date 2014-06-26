# -*- coding: utf-8 -*-
import re
import random
import time
import datetime
from lxml import etree
from xml.dom import minidom 
from django.conf import settings
from django.views.generic import View
from shopapp.weixin.models import WeiXinAccount,WeiXinAutoResponse,WeiXinUser,\
    WX_TEXT,WX_IMAGE,WX_VOICE,WX_VIDEO,WX_LOCATION,WX_LINK,WX_EVENT,\
    WX_EVENT_CLICK,WX_EVENT_SUBSCRIBE,WX_EVENT_UNSUBSCRIBE,WX_EVENT_SCAN,\
    WX_EVENT_LOCATION,WX_EVENT_VIEW
from .weixin_apis import WeiXinAPI
from shopback.logistics import getLogisticTrace
from shopback import paramconfig as pcfg
from common.utils import parse_datetime,format_datetime
import logging

logger = logging.getLogger('django.request')
VALID_MOBILE_REGEX = '^1[3458][0-9]{9}'
VALID_CODE_REGEX   = '^[0-9]{6}$'
VALID_EVENT_CODE   = '^[qwertyuiopQWERTYUIOP]$'

mobile_re = re.compile(VALID_MOBILE_REGEX)
code_re   = re.compile(VALID_CODE_REGEX)
event_re  = re.compile(VALID_EVENT_CODE)

class MessageException(Exception):
    
    def __init__(self,message=None):
        self.message  = message
  
    def __str__(self):
        return self.message
    

class WeixinUserService():
    
    _wx_api = None
    _wx_user    = None
    
    def __init__(self,openId=None):
        
        self._wx_api = WeiXinAPI()
        if openId:
            self._wx_user = getOrCreateUser(openId)
        self._wx_user = self._wx_user or WeiXinUser.getAnonymousWeixinUser()
        
    def getOrCreateUser(self,openId,force_update=False):
        
        wx_user,state =  WeiXinUser.objects.get_or_create(openid=openId) 
        if state or force_update:     
            userinfo = self. _wx_api.getUserInfo(openId)
           
            for k,v in userinfo.iteritems():
                setattr(wx_user,k,v)
                
            wx_user.subscribe_time = datetime.datetime.fromtimestamp(
                                    userinfo.get('subscribe_time'))
            wx_user.save()
        
        return wx_user
    
    def setOpenId(self,openId):
        self._wx_user = self.getOrCreateUser(openId)      
    
    def checkSignature(self,signature,timestamp,nonce):
        return self._wx_api.checkSignature(signature,timestamp,nonce)
    
    def activeAccount(self):
        self._wx_api._wx_account.activeAccount()
    
    def mergeMessageKey(self,doc,xmld,key):
        
        xmlCnt = doc.xpath('/xml/%s'%key)
        if xmlCnt:
            xmld.update({key:xmlCnt[0].text})
    
    def parseXML2Param(self,xmlc):
        
        doc     = etree.fromstring(xmlc)
        createtime_stamp = int(doc.xpath('/xml/CreateTime')[0].text)
        msgtype = doc.xpath('/xml/MsgType')[0].text
        
        xmld   = {  
                    'CreateTime':datetime.datetime.fromtimestamp(createtime_stamp),
                    'MsgType':msgtype,
                 }
        merge_fields = ['FromUserName','ToUserName','CreateTime','MsgType','Content',
                        'MsgId','PicUrl','MediaId','Format','MediaId','ThumbMediaId',
                        'Location_X','Location_Y','Scale','Label','Title','Description',
                        'Url','EventKey','Event','Ticket','Latitude','Longitude',
                        'Precision']
        
        for field in merge_fields:
            self.mergeMessageKey(doc, xmld, field)
        
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
    
    def genValidCode(self):
        return str(random.randint(100000,999999))
        
    def getValidCode(self,mobile,openId):
        
        wx_user   = self.getOrCreateUser(openId,force_update=True)
        
        if not  wx_user.is_code_time_safe():      
            raise MessageException(u'请%d秒后重新发送'%(wx_user.get_wait_time()))
        
        validCode = self.genValidCode()
        self.sendValidCode(mobile,validCode)        
        
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
             raise MessageException(u'验证码不对，请重新输入:')
             
         wx_user.isvalid = True
         wx_user.save()
         return True
    
    def getResponseByBestMatch(self,message,openId,*args,**kwargs):
        
        if mobile_re.match(message) and self.getValidCode(message,openId):
            return WeiXinAutoResponse.objects.get_or_create(message=u'校验码提醒')[0]
        
        if code_re.match(message) and self.checkValidCode(message,openId):
            return WeiXinAutoResponse.objects.get_or_create(message=u'校验成功提示')[0]            
            
        for resp in self.getResponseList():
            if message.rfind(resp.message.strip()) > -1:
                return resp
            
        return WeiXinAutoResponse.respDefault()
        
    def getTrade2BuyerStatus(self,status,sys_status):
        
        if status == pcfg.TRADE_FINISHED:
            return u'宝贝已签收'
        if status != pcfg.TRADE_FINISHED and sys_status == pcfg.FINISHED_STATUS:
            return u'宝贝已发出'
        if status == pcfg.WAIT_BUYER_CONFIRM_GOODS and sys_status != pcfg.FINISHED_STATUS:
            return u'宝贝正在挑选中'
        if sys_status == pcfg.WAIT_PREPARE_SEND_STATUS:
            return u'订单已收到,准备发出'
        if sys_status == pcfg.WAIT_AUDIT_STATUS:
            return u'订单正在审核'
        return u'订单好像出问题了'
    
    def genTextRespJson(self,text):
        return  { 'MsgType':WX_TEXT,
                  'Content':text}
    
    def sendValidCode(self,mobile,validCode,title=u'微信手机验证'):
        
        from shopapp.smsmgr import sendMessage
        
        msgTemplate = u"验证码:%s,优尼世界提醒您，绑定手机后，可以查询最近一次订单，"+\
            u"及物流信息，还可以填写宝宝档案，填写后您的宝宝可能会收到幸运礼物哦!【优尼世界】"
        return sendMessage(mobile,title,msgTemplate%validCode)
    
    def formatJsonToPrettyString(self,jsonContent):
        assert type(jsonContent) in (list,tuple)
        
        jsonStrArray = []
        for a in jsonContent:
            if type(a[1]) not in (list,tuple):
                jsonStrArray.extend([a[0],'\n\t',a[1],'\n'])
                continue
            jsonStrArray.extend([a[0],'\n'])
            for l in a[1]:
                if type(l) not in (tuple,list):
                    jsonStrArray.extend(['\t',l,'\n'])
                    continue
                jsonStrArray.extend([l[0],'\n\t',l[1],'\n'])
        return ''.join(jsonStrArray)
            
    
    def getLatestTradeByMobile(self,mobile):
        
        from shopback.trades.models import MergeTrade
        latest_trades = MergeTrade.objects.filter(
                            receiver_mobile=mobile)\
                            .order_by('-pay_time')
        if latest_trades.count() == 0:
            raise MessageException(u'你还没有交易记录哦')
        return latest_trades[0]
    
    def getTradeMessageByMobile(self,mobile):
        
        trade_array = []
        
        trade = self.getLatestTradeByMobile(mobile)
        
        trade_array.append(('旺旺ID', trade.buyer_nick))
        trade_array.append(('成交时间', trade.pay_time and format_datetime(trade.pay_time)))
        trade_array.append(('订单状态', self.getTrade2BuyerStatus(trade.status,trade.sys_status)))
        orders = []
        for order in trade.merge_orders.filter(sys_status=pcfg.IN_EFFECT):
            orders.append(order.getSimpleName())
        trade_array.append(('订单详细', orders))
        
        return self.genTextRespJson(self.formatJsonToPrettyString(trade_array))
        
        
    def getLogisticMessageByMobile(self,mobile):
        
        trade = self.getLatestTradeByMobile(mobile)
        if not trade.out_sid or not trade.logistics_company:
            raise MessageException(u'客官稍安勿燥，宝贝正在准备中...')
             
        trade_traces = getLogisticTrace(trade.out_sid,trade.logistics_company.code.split('_')[0])
        
        return self.genTextRespJson(self.formatJsonToPrettyString(trade_traces))
        
    def handleEvent(self,eventKey,openId,eventType=WX_EVENT_CLICK):
        
        if self._wx_user.isNone():
            raise MessageException(u'没有该用户信息')
        
        if eventKey in ('Q','W','E','R') and not self._wx_user.isValid():
            raise MessageException(u'你还没有绑定手机哦!\n请输入手机号:')
        
        if eventKey in ("Q","R"):
            raise MessageException(u'功能还没有准备好哦')
            
        elif  eventKey == "W":
            return self.getTradeMessageByMobile(self._wx_user.mobile)
            
        elif  eventKey == "E":
            return self.getLogisticMessageByMobile(self._wx_user.mobile)
        
        if eventType == WX_EVENT_SUBSCRIBE :
            self._wx_user.doSubscribe(eventKey.rfind('_') > -1 and eventKey.split('_')[1] or '')
            
        if eventType == WX_EVENT_UNSUBSCRIBE:
            self._wx_user.unSubscribe()
            
        return self.getResponseByBestMatch(eventKey,openId).autoParams()
            
        
    def handleRequest(self,params):
        
        openId     = params['FromUserName']
        msgtype  = params['MsgType']
        
        self.setOpenId(openId)
        ret_params = {'ToUserName':params['FromUserName'],
                      'FromUserName':params['ToUserName'],
                      'CreateTime':int(time.time())}
        
        try:
            if msgtype == WX_EVENT:
                ret_params.update(self.handleEvent(params['EventKey'].upper(), 
                                                   openId,eventType=params['Event']))
                return ret_params
                
            matchMsg = ''
            if msgtype   == WX_TEXT: 
                matchMsg = params['Content']
                if event_re.match(matchMsg):
                    ret_params.update(self.handleEvent(matchMsg.upper(),openId))
                    return ret_params
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
            
            resp = self.getResponseByBestMatch(matchMsg.strip(),openId)
            ret_params.update(resp.autoParams())
        except MessageException,exc:
            ret_params.update(self.genTextRespJson(exc.message))
        except Exception,exc:
            logger.error(exc.message or 'weixin response error',exc_info=True)
            ret_params.update(self.genTextRespJson(u'不好了，小优尼闹情绪不想干活了！'))
            
        return ret_params
    
    
    
