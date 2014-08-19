# -*- coding: utf-8 -*-
import re
import random
import time
import datetime
from lxml import etree
from xml.dom import minidom 
from django.conf import settings
from django.views.generic import View
from shopapp.weixin.models import (WeiXinAccount,
                                   WeiXinAutoResponse,
                                   WeiXinUser,
                                   WXProduct,
                                   WXOrder,
                                   WXLogistic)
from .weixin_apis import WeiXinAPI
from shopback.base.service import LocalService
from shopback.logistics import getLogisticTrace
from shopback.items.models import Product
from shopback.users.models import User
from shopback.trades.handlers import trade_handler
from shopback.trades.models import MergeTrade,MergeOrder
from shopback import paramconfig as pcfg
from common.utils import parse_datetime,format_datetime,replace_utf8mb4,update_model_fields
import logging

logger = logging.getLogger('django.request')
VALID_MOBILE_REGEX = '^1[34578][0-9]{9}'
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
    

def parseXMLElement(sub_elem):
        
    if sub_elem.tag == 'CreateTime':
        return {sub_elem.tag:datetime.datetime.
                fromtimestamp(int(sub_elem.text))}
        
    return {sub_elem.tag:sub_elem.text}
    
def parseXML2Param(xmlc):
    
    doc     = etree.fromstring(xmlc)
    root_elem = doc.xpath('/xml')[0]
    xmld   = {}
    
    for sub_elem in root_elem.iterchildren():
        xmld.update(parseXMLElement(sub_elem))
    
    return xmld

def buildDomByJson(parentDom,djson,arrayTag='',rootTag=''):
    
    pdom = parentDom
    doc  = parentDom.ownerDocument or parentDom
    if rootTag:
        pdom = doc.createElement(rootTag)
        parentDom.appendChild(pdom)
        
    json_type = type(djson)
    if json_type == dict:
        
        for k,v in djson.iteritems():
            if type(v) in (list,tuple):
                buildDomByJson(pdom,v,arrayTag=k)
            else:
                dict_dom = doc.createElement(k)
                pdom.appendChild(dict_dom)
                buildDomByJson(dict_dom,v)                
        return
        
    if json_type in (list,tuple):
        
        if not arrayTag:
            raise Exception(u'数组类型需要指定父标签')
        
        for ajson in djson:
            buildDomByJson(pdom,ajson,rootTag=arrayTag)
        return 
    
    if json_type in (str,unicode):
        
        pdom.appendChild(doc.createCDATASection(djson))
        return 
    
    if json_type in (int,float):
        
        pdom.appendChild(doc.createTextNode(str(djson)))
        return
    

def formatParam2XML(params):  
    """ 
    """      
    dom = minidom.Document()
    initStr = dom.toxml()
    
    buildDomByJson(dom, params ,rootTag='xml')
    x = dom.toxml()
    return x[len(initStr):]


class WeixinUserService():
    
    _wx_api = None
    _wx_user    = None
    
    def __init__(self,openId=None):
        
        self._wx_api = WeiXinAPI()
        if openId:
            self._wx_user = self.getOrCreateUser(openId)
        
        if not self._wx_user:
            self._wx_user = WeiXinUser.getAnonymousWeixinUser()
        
    def getOrCreateUser(self,openId,force_update=False):
        
        wx_user,state =  WeiXinUser.objects.get_or_create(openid=openId) 
        if state or force_update:
            try:     
                userinfo = self. _wx_api.getUserInfo(openId)
                
                for k,v in userinfo.iteritems():
                    hasattr(wx_user,k) and setattr(wx_user,k,v or getattr(wx_user,k))
                
                wx_user.nickname = replace_utf8mb4(wx_user.nickname.decode('utf8'))
                subscribe_time = userinfo.get('subscribe_time',None)
                if subscribe_time:
                    wx_user.subscribe_time = datetime.datetime\
                        .fromtimestamp(int(subscribe_time))
                        
                wx_user.save()
            except Exception,exc:
                logger.error(u'获取微信用户信息错误:%s'%exc.message,exc_info=True)
                
        return wx_user
    
    def setOpenId(self,openId):
        self._wx_user = self.getOrCreateUser(openId)      
    
    def checkSignature(self,signature,timestamp,nonce):
        return self._wx_api.checkSignature(signature,timestamp,nonce)
    
    def activeAccount(self):
        self._wx_api._wx_account.activeAccount()
    
    def getResponseList(self):
        
        return WeiXinAutoResponse.objects.extra(
                    select={'length':'Length(message)'}).order_by('-length')
    
    def genValidCode(self):
        return str(random.randint(100000,999999))
        
    def getValidCode(self,mobile,openId):
        
        wx_users = WeiXinUser.objects.filter(mobile=mobile,
                                             isvalid=True).exclude(openid=openId)
        if wx_users.count() > 0:
            raise MessageException(u'该手机已被其他用户绑定.')
        
        wx_user   = self.getOrCreateUser(openId,force_update=True)
        
        if wx_user.mobile.strip() == mobile.strip() and wx_user.isValid():
            raise MessageException(u'您的手机号无需重新绑定，如有问题请点击【我的】->【联系客服】.')
        
        if not  wx_user.is_code_time_safe():      
            raise MessageException(u'请%d秒后重新发送'%(wx_user.get_wait_time()))
        
        if wx_user.mobile == mobile:
            
            wx_user.vmobile   = mobile
            wx_user.isvalid   = True
            wx_user.save()
            raise MessageException(WeiXinAutoResponse.objects.get(message=u'校验成功提示').content)  
        
        valid_code = self.genValidCode()
        self.sendValidCode(mobile,valid_code)        
        
        wx_user.vmobile   = mobile
        wx_user.isvalid   = False
        wx_user.validcode = valid_code
        wx_user.valid_count += 1
        wx_user.code_time = datetime.datetime.now()
        wx_user.save()
        
        return valid_code
    
    def checkValidCode(self,validCode,openId):
        
         wx_user   = self.getOrCreateUser(openId)
         if wx_user.isvalid:
             return True
             
         if not wx_user.validcode or wx_user.validcode != validCode:
             raise MessageException(u'验证码不对，请重新输入:')
         
         wx_user.mobile  = wx_user.vmobile
         wx_user.isvalid = True
         wx_user.save()
         return True
    
    def getResponseByBestMatch(self,message,openId,*args,**kwargs):
        
        if mobile_re.match(message) and self.getValidCode(message,openId):
            return WeiXinAutoResponse.objects.get_or_create(message=u'校验码提醒')[0].autoParams()
        
        if code_re.match(message) and self.checkValidCode(message,openId):
            return WeiXinAutoResponse.objects.get_or_create(message=u'校验成功提示')[0].autoParams()            
        
        if message == '0' and self._wx_user.isValid():
            return self.genTextRespJson(u'您已经成功绑定手机，取消绑定请输入[q]\n修改绑定请重新输入手机号：')
        
        for resp in self.getResponseList():
            if message.rfind(resp.message.strip()) > -1:
                return resp.autoParams()
            
        return WeiXinAutoResponse.respDKF()
        
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
        return  { 'MsgType':WeiXinAutoResponse.WX_TEXT,
                  'Content':text}
    
    def sendValidCode(self,mobile,validCode,title=u'微信手机验证'):
        
        from shopapp.smsmgr import sendMessage
        
        wx_resp = WeiXinAutoResponse.objects.get_or_create(message='SJYZM')[0]
        msgTemplate = wx_resp.content
        
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
        
        trade_array.append((u'昵称', trade.buyer_nick))
        trade_array.append((u'成交时间', trade.pay_time and format_datetime(trade.pay_time)))
        trade_array.append((u'订单状态', self.getTrade2BuyerStatus(trade.status,trade.sys_status)))
        orders = []
        for order in trade.merge_orders.filter(sys_status=pcfg.IN_EFFECT):
            orders.append(order.getSimpleName())
        trade_array.append((u'订单详细', orders))
        
        return self.genTextRespJson(self.formatJsonToPrettyString(trade_array))
        
        
    def getLogisticMessageByMobile(self,mobile):
        
        trade = self.getLatestTradeByMobile(mobile)
        if not trade.out_sid or not trade.logistics_company:
            raise MessageException(u'亲请稍安勿燥，宝贝正在准备出库中...')
             
        trade_traces = getLogisticTrace(trade.out_sid,
                                        trade.logistics_company.code.split('_')[0])
        
        return self.genTextRespJson(self.formatJsonToPrettyString(trade_traces))

    def getReferalProgramWelcomeMessage(self, mobile):
        msg = "把优尼世界推荐给您的朋友，你们双方都将有机会获得额外的返利。\n\n请输入您朋友的姓氏和她的手机号,用#号连接：\n(例如：李#13801235666)"
        return self.genTextRespJson(msg)

    def addReferal(self, referal_from_mobile, refral_to_mobile, referal_to_lastname):
        user_exits_num = Customer.objects.filter(mobile=referal_to_mobile).count()
        
        if user_exists_num > 0:
            return False
        
        Customer.objects.create(mobile=referal_to_mobile)

        ReferalRelationship.objects.create(
            referal_from_mobile=referal_from_mobile, 
            referal_to_mobile=referal_to_mobile, 
            referal_to_lastname=referal_to_lastname
            )
        
        return True
    
    
    def handleEvent(self,eventKey,openId,eventType=WeiXinAutoResponse.WX_EVENT_CLICK):
        
        if self._wx_user.isNone():
            raise MessageException(u'用户信息获取异常')
        
        eventKey = eventKey.upper()
        
        if eventKey in ('Q','W','E','R', 'Z') and not self._wx_user.isValid():
            raise MessageException(u'你还没有绑定手机哦!\n请输入手机号:')
        
        if eventKey == "Q":
            
            self._wx_user.isvalid = False
            self._wx_user.save()
            raise MessageException(u'您的手机已取消绑定，重新绑定请输入[0]。')
            
        elif  eventKey == "W":
            return self.getTradeMessageByMobile(self._wx_user.mobile)
            
        elif  eventKey == "E":
            return self.getLogisticMessageByMobile(self._wx_user.mobile)
        
        elif eventKey == "Z":
            return self.getReferalProgramWelcomeMessage(self._wx_user.mobile)

        if eventType == WeiXinAutoResponse.WX_EVENT_SUBSCRIBE :
            self._wx_user.doSubscribe(eventKey.rfind('_') > -1 and eventKey.split('_')[1] or '')
            return WeiXinAutoResponse.respDefault()
            
        elif eventType == WeiXinAutoResponse.WX_EVENT_UNSUBSCRIBE:
            self._wx_user.unSubscribe()
            
        return self.getResponseByBestMatch(eventKey,openId)
    
    def handleMerchantOrder(self,user_id,order_id,order_status=2,product_id='',sku_info=''):   
        
        from shopback.trades.service import TradeService
        
        TradeService.createTrade(user_id,order_id,pcfg.WX_TYPE)
        
        return self.genTextRespJson(u'您的订单(%s)优尼世界已收到,我们会尽快将宝贝寄给您。'%
                                                                order_id)
        
    def handleRequest(self,params):
        
        openId     = params['FromUserName']
        msgtype  = params['MsgType']
        
        self.setOpenId(openId)
        ret_params = {'ToUserName':params['FromUserName'],
                      'FromUserName':params['ToUserName'],
                      'CreateTime':int(time.time())}
        
        try:
            if msgtype == WeiXinAutoResponse.WX_EVENT:
                
                eventType=params['Event']
                if eventType == WeiXinAutoResponse.WX_EVENT_ORDER:
                    ret_params.update(self.handleMerchantOrder(params['ToUserName'],
                                                                params['OrderId'],
                                                                params['OrderStatus'],
                                                                params['ProductId'],
                                                                params['SkuInfo']))
                    
                elif eventType == WeiXinAutoResponse.WX_EVENT_LOCATION:    
                    ret_params.update(self.genTextRespJson(
                                    u'你的地理位置（%s,%s）.'%
                                    (params['Latitude'],params['Longitude'])))
                else:
                    ret_params.update(self.handleEvent(params['EventKey'].upper(), 
                                                       openId,eventType=params['Event']))
                    
                return ret_params
                
            matchMsg = ''
            if msgtype   == WeiXinAutoResponse.WX_TEXT: 
                matchMsg = params['Content']
                if event_re.match(matchMsg):
                    ret_params.update(self.handleEvent(matchMsg.upper(),openId))
                    return ret_params
                
            elif msgtype == WeiXinAutoResponse.WX_IMAGE:
                matchMsg = u'图片'
            elif msgtype == WeiXinAutoResponse.WX_VOICE:
                matchMsg = u'语音'
            elif msgtype == WeiXinAutoResponse.WX_VIDEO:
                matchMsg = u'视频'
            elif msgtype == WeiXinAutoResponse.WX_LOCATION:
                matchMsg = u'位置'
            else:
                matchMsg = u'链接'
            
            resp = self.getResponseByBestMatch(matchMsg.strip(),openId)
            ret_params.update(resp)
        except MessageException,exc:
            ret_params.update(self.genTextRespJson(exc.message))
            
        except Exception,exc:
            logger.error(u'微信请求异常:%s'%exc.message ,exc_info=True)
            ret_params.update(self.genTextRespJson(u'不好了，小优尼闹情绪不想干活了！'))
            
        return ret_params
    

class WxShopService(LocalService):
    
    order  = None
    wx_api = None
    
    def __init__(self,t):
        assert t not in ('',None)
        
        if isinstance(t,WXOrder):
            self.order = t
        else:
            self.order   = WXOrder.objects.get(order_id=t)
            
        self.wx_api = WxShopService.getWXApiInstance()
        
    @classmethod
    def getWXApiInstance(cls):
        
        return WeiXinAPI()
    
    @classmethod
    def createTradeByDict(cls,user_id,order_dict):
        
        order,state = WXOrder.objects.get_or_create(order_id=order_dict['order_id'],
                                                    seller_id=user_id)
        
        for k,v in order_dict.iteritems():
            hasattr(order,k) and setattr(order,k,v)
        
        order.buyer_nick = replace_utf8mb4(order_dict['buyer_nick'])
        order.order_create_time = datetime.datetime.fromtimestamp(
            int(order_dict['order_create_time']))
        order.save()
        
        return order
    
    @classmethod
    def createTrade(cls,user_id,tid,*args,**kwargs):
        
        order_id    = tid
        wx_api      = cls.getWXApiInstance()
        
        order_dict  = wx_api.getOrderById(order_id)
        
        order = cls.createTradeByDict(user_id, order_dict)
        
        return order
    
    @classmethod
    def createMergeOrder(cls,merge_trade,order,*args,**kwargs):
        
        merge_order,state = MergeOrder.objects.get_or_create(oid=order.order_id,
                                                             merge_trade = merge_trade)
        state = state or not merge_order.sys_status
        
        if order.order_status == WXOrder.WX_FEEDBACK:
            refund_status = pcfg.REFUND_WAIT_SELLER_AGREE
        else:
            refund_status = pcfg.NO_REFUND
        
        if (order.order_status == WXOrder.WX_CLOSE):
            sys_status = pcfg.INVALID_STATUS
        else:
            sys_status = merge_order.sys_status or pcfg.IN_EFFECT
        
        if state:
            wx_product = WXProduct.objects.getOrCreate(order.product_id)
            sku_list = wx_product.sku_list
            
            product_code = ''
            if len(sku_list) == 1 and not sku_list[0]['sku_id']:
                product_code = sku_list[0]['product_code']
            else:
                for sku in sku_list:
                    if sku['sku_id'] == order.product_sku:
                        product_code = sku['product_code']
                        break
            
            outer_id,outer_sku_id = Product.objects.trancecode(product_code,'',
                                                               sku_code_prior=True)
              
            merge_order.payment = order.order_total_price/100.0
            merge_order.created = order.order_create_time
            merge_order.num     = order.product_count
            merge_order.title   = order.product_name
            merge_order.pic_path = order.product_img
            merge_order.outer_id = outer_id
            merge_order.outer_sku_id = outer_sku_id
       
        merge_order.refund_status = refund_status
        merge_order.status = WXOrder.mapOrderStatus(order.order_status)
        merge_order.sys_status = sys_status
        
        merge_order.save()
        
        return merge_order
    
    
    @classmethod
    def createMergeTrade(cls,trade,*args,**kwargs):
        
        user = User.objects.get(visitor_id=trade.seller_id)
        merge_trade,state = MergeTrade.objects.get_or_create(user=user,
                                                             tid=trade.order_id)
        
        update_fields = ['buyer_nick','created','pay_time','modified','status']
        
        merge_trade.buyer_nick = trade.buyer_nick
        merge_trade.created  = trade.order_create_time
        merge_trade.modified = trade.order_create_time
        merge_trade.pay_time = trade.order_create_time
        merge_trade.status   = WXOrder.mapTradeStatus(trade.order_status) 
        
        update_address = False
        if not merge_trade.receiver_name and trade.receiver_name:
            
            update_address  = True
            merge_trade.receiver_name  = trade.receiver_name
            merge_trade.receiver_state = trade.receiver_province
            merge_trade.receiver_city  = trade.receiver_city
            merge_trade.receiver_district  = trade.receiver_zone
            merge_trade.receiver_address  = trade.receiver_address
            merge_trade.receiver_mobile   = trade.receiver_mobile
            merge_trade.receiver_phone    = trade.receiver_phone 
            
            address_fields = ['receiver_name','receiver_state','receiver_district',
                             'receiver_city','receiver_address',
                             'receiver_mobile','receiver_phone']
            
            update_fields.extend(address_fields)
            
        merge_trade.payment      = (merge_trade.payment or 
                                    round(trade.order_total_price/100.0,2))
        merge_trade.total_fee    = (merge_trade.total_fee or 
                                    round(trade.product_price/100.0,2)*trade.product_count)
        merge_trade.post_fee     = (merge_trade.post_fee or 
                                    round(trade.order_express_price/100.0,2))
        
        merge_trade.trade_from    = MergeTrade.trade_from.WAP
        merge_trade.shipping_type = pcfg.EXPRESS_SHIPPING_TYPE
        merge_trade.type          = pcfg.WX_TYPE

        update_model_fields(merge_trade,update_fields=update_fields
                            +['shipping_type','type','payment',
                              'total_fee','post_fee','trade_from'])
        
        cls.createMergeOrder(merge_trade,trade)
        
        trade_handler.proccess(merge_trade,
                               **{'origin_trade':trade,
                                  'update_address':(update_address and 
                                                    merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS),
                                  'first_pay_load':(
                                    merge_trade.sys_status == pcfg.EMPTY_STATUS and 
                                    merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS)})
        
        return merge_trade
    
    def payTrade(self,*args,**kwargs):
        
        trade = self.__class__.createTrade(self.order.seller_id,
                                          self.order.order_id)
        
        return WxShopService.createMergeTrade(trade)
    
    def sendTrade(self,company_code=None,out_sid=None,retry_times=3,*args,**kwargs):
        
        try:
            wx_logistic = WXLogistic.objects.get(origin_code__icontains
                                                 =company_code.split('_')[0])
            
            response = self.wx_api.deliveryOrder(self.order.order_id,
                                                 wx_logistic.company_code,
                                                 out_sid)
        except Exception,exc:
            logger.error(u'微信发货失败:%s'%exc.message,exc_info=True)
            raise exc



