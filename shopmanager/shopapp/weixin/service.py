# -*- coding: utf-8 -*-
import re
import random
import time
import datetime
import json
from lxml import etree
from xml.dom import minidom
from django.core.cache import cache
from django.conf import settings
from django.views.generic import View
from shopapp.weixin.models import (
    WeiXinAccount,
    WeiXinAutoResponse,
    WeiXinUser,
    WXProduct,
    WXOrder,
    WXLogistic,
    VipCode
)
from flashsale.xiaolumm.models import XiaoluMama
from shopapp.weixin.models import WeixinUnionID
from shopapp.weixin.models_base import WeixinFans
from .weixin_apis import WeiXinAPI
from shopback.base.service import LocalService
from shopback.logistics import getLogisticTrace
from shopback.logistics.models import LogisticsCompany
from shopback.items.models import Product
from shopback.users.models import User
from shopback.trades.handlers import trade_handler
from shopback.trades.models import MergeTrade, MergeOrder
from shopback import paramconfig as pcfg
from common.utils import parse_datetime, format_datetime, replace_utf8mb4, update_model_fields, xml2dict
from shopapp.signals import weixin_verifymobile_signal
from shopapp.weixin import tasks

import logging

logger = logging.getLogger('django.request')
VALID_MOBILE_REGEX = '^1[34578][0-9]{9}$'
VALID_CODE_REGEX = '^[0-9]{6,7}$'
VALID_EVENT_CODE = '^[qwertyuiopknQWERTYUIOPKN]$'
WX_MESSAGE_TIMEOUT = 30

mobile_re = re.compile(VALID_MOBILE_REGEX)
code_re = re.compile(VALID_CODE_REGEX)
event_re = re.compile(VALID_EVENT_CODE)


class MessageException(Exception):
    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return self.message


def parseXMLElement(sub_elem):
    if sub_elem.tag == 'CreateTime':
        return {sub_elem.tag: datetime.datetime.
            fromtimestamp(int(sub_elem.text))}

    return {sub_elem.tag: sub_elem.text}


def parseXML2Param(xmlc):
    sdict = xml2dict.parse(xmlc)
    djson = json.loads(json.dumps(sdict))
    xml_json = djson.get('xml', {})

    if xml_json.has_key('CreateTime'):
        xml_json['CreateTime'] = datetime.datetime.fromtimestamp(
            int(xml_json['CreateTime']))

    return xml_json


def buildDomByJson(parentDom, djson, arrayTag='', rootTag=''):
    pdom = parentDom
    doc = parentDom.ownerDocument or parentDom
    if rootTag:
        pdom = doc.createElement(rootTag)
        parentDom.appendChild(pdom)

    json_type = type(djson)
    if json_type == dict:
        for k, v in djson.iteritems():
            if type(v) in (list, tuple):
                buildDomByJson(pdom, v, arrayTag=k)
            else:
                dict_dom = doc.createElement(k)
                pdom.appendChild(dict_dom)
                buildDomByJson(dict_dom, v)
        return

    if json_type in (list, tuple):
        if not arrayTag:
            raise Exception(u'数组类型需要指定父标签')

        for ajson in djson:
            buildDomByJson(pdom, ajson, rootTag=arrayTag)
        return

    if json_type in (str, unicode):
        pdom.appendChild(doc.createCDATASection(djson))
        return

    if json_type in (int, float):
        pdom.appendChild(doc.createTextNode(str(djson)))
        return


def formatParam2XML(params):
    """
    """
    if type(params) != dict:
        return '%s' % params

    dom = minidom.Document()
    initStr = dom.toxml()

    buildDomByJson(dom, params, rootTag='xml')
    x = dom.toxml()
    return x[len(initStr):]


def handleWeiXinMenuRequest(openid, wxpubId, event, eventKey):
    """ 2016-4-3 微信公众号常见问题请求处理 """
    from_username = openid
    to_username   = wxpubId
    ret_params = {'ToUserName': from_username,
                  'FromUserName': to_username,
                  'CreateTime': int(time.time())}
    try:
        eventKey = eventKey.upper()
        if eventKey == 'FAQS':
            faq_responses = WeiXinAutoResponse.objects.filter(rtype=WeiXinAutoResponse.WX_NEWS, message=eventKey)
            if faq_responses.count() > 0:
                faq = faq_responses[0]
                ret_params.update(faq.respNews())
                return ret_params

        if eventKey == 'MAMA_REFERAL_QRCODE' or \
           event == WeiXinAutoResponse.WX_EVENT_SCAN.lower() or \
           event == WeiXinAutoResponse.WX_EVENT_SUBSCRIBE.lower():
            tasks.task_create_mama_referal_qrcode_and_response_weixin.delay(to_username, from_username, event, eventKey)
            ret_params.update({
                'MsgType': WeiXinAutoResponse.WX_TEXT,
                'Content': u'[玫瑰]亲，这是您的专属二维码，快告诉好友来开店赚佣金吧！'
            })

        if eventKey == 'MAMA_MANAGER_QRCODE':
            tasks.task_create_mama_and_response_manager_qrcode.delay(to_username, from_username, event, eventKey)
            ret_params.update({
                'MsgType': WeiXinAutoResponse.WX_TEXT,
                'Content': u'[爱心]亲，请长按识别图中二维码, 添加您的专属管理员微信:'
            })

    except Exception, exc:
        logger.error(u'handleWeiXinMenuRequest error: %s' % exc.message, exc_info=True)
        ret_params.update({
            'MsgType': WeiXinAutoResponse.WX_TEXT,
            'Content': u'Sorry亲，系统负载太高，请稍等！[撇嘴]'
        })

    return ret_params



def handleWeiXinSubscribeEvent(params, wx_api):
    """
    处理关注／取关事件
    """
    openid = params.get('FromUserName')
    event = params.get('Event')
    app_key = wx_api.getAccount().app_id

    if event == 'subscribe':
        user_info = wx_api.getCustomerInfo(openid)
        unionid = user_info['unionid']
        fans = WeixinFans.objects.filter(app_key=app_key, openid=openid).first()
        if not fans:
            fans = WeixinFans()
        fans.openid = openid
        fans.app_key = app_key
        fans.unionid = unionid
        fans.subscribe = True
        fans.subscribe_time = datetime.datetime.now()
        fans.save()
    elif event == 'unsubscribe':
        fans = WeixinFans.objects.filter(app_key=app_key, openid=openid).first()
        if fans:
            fans.subscribe = False
            fans.unsubscribe_time = datetime.datetime.now()
            fans.save()

class WeixinUserService():
    _wx_api = None
    _wx_user = None

    def __init__(self, appKey, openId=None, unionId=None):

        self._wx_api = WeiXinAPI()
        self._wx_api.setAccountId(appKey=appKey)
        if openId:
            self._wx_user = self.getOrCreateUser(openId, unionId=unionId)
        if not self._wx_user:
            self._wx_user = WeiXinUser.getAnonymousWeixinUser()

    def getOrCreateUser(self, openId, unionId=None, appkey=None, force_update=False):
        if unionId:
            try:
                return WeiXinUser.objects.get(unionid=unionId)
            except:
                pass
        if not appkey != settings.WEIXIN_APPID:
            raise Exception('not valid weixin auth:appkey=%s, openid=%s, unionid=%s'% (appkey, openId, unionId))
        wx_user, state = WeiXinUser.objects.get_or_create(openid=openId)
        if state or force_update or not wx_user.unionid:
            from .tasks import task_Update_Weixin_Userinfo
            task_Update_Weixin_Userinfo.delay(openId, unionId=unionId)
        return wx_user

    def setOpenId(self, openId):
        self._wx_user = self.getOrCreateUser(openId)

    def checkSignature(self, signature, timestamp, nonce):
        return self._wx_api.checkSignature(signature, timestamp, nonce)

    def activeAccount(self):
        self._wx_api._wx_account.activeAccount()

    def genValidCode(self, force_update=False):
        if not force_update and self._wx_user.validcode:
            return self._wx_user.validcode
        return str(random.randint(100000, 999999))

    def getValidCode(self, mobile, openId):

        wx_users = WeiXinUser.objects.filter(mobile=mobile,
                                             isvalid=True).exclude(openid=openId)
        if wx_users.count() > 0:
            raise MessageException(u'该手机已被其他用户绑定.')

        wx_user = self.getOrCreateUser(openId, force_update=True)

        if wx_user.mobile.strip() == mobile.strip() and wx_user.isValid():
            raise MessageException(u'您的手机号无需重新绑定，如有问题请点击【我的】->【联系客服】.')

        if not wx_user.is_code_time_safe():
            raise MessageException(u'请%d秒后重新发送' % (wx_user.get_wait_time()))

        if wx_user.mobile == mobile:
            wx_user.vmobile = mobile
            wx_user.isvalid = True
            wx_user.save()
            valid_resp = WeiXinAutoResponse.objects.get(message=u'校验成功提示')
            raise MessageException(valid_resp.content.replace('\r', ''))

        if not wx_user.is_valid_count_safe():
            raise MessageException(u'[撇嘴]您的手机验证次数达到上限，请联系客服帮您处理！')

        mobile_change = wx_user.vmobile != mobile
        valid_code = self.genValidCode(force_update=mobile_change)
        self.sendValidCode(mobile, valid_code)

        wx_user.vmobile = mobile
        wx_user.isvalid = False
        wx_user.validcode = valid_code
        wx_user.valid_count += 1
        wx_user.code_time = datetime.datetime.now()
        wx_user.save()

        return valid_code

    def checkValidCode(self, validCode, openId):

        wx_user = self.getOrCreateUser(openId)
        if wx_user.isvalid:
            return True

        if not wx_user.validcode or wx_user.validcode != validCode:
            raise MessageException(u'验证码不对，请重新输入:')

        wxusers = WeiXinUser.objects.filter(mobile=wx_user.vmobile).exclude(openid=openId)
        if wxusers.count() > 0:
            raise MessageException(u'该手机号码已被其他用户验证。')

        wx_user.mobile = wx_user.vmobile or wx_user.mobile
        wx_user.isvalid = True
        wx_user.valid_count = 0
        wx_user.save()

        VipCode.objects.genVipCodeByWXUser(wx_user)

        weixin_verifymobile_signal.send(sender=WeiXinUser, user_openid=openId)

        return True

    def getResponseByBestMatch(self, message, openId, *args, **kwargs):

        if mobile_re.match(message):
            wx_user = self.getOrCreateUser(openId, force_update=True)
            if wx_user.isValid():
                return WeiXinAutoResponse.respDKF()

            if self.getValidCode(message, openId):
                return WeiXinAutoResponse.objects.get_or_create(message=u'校验码提醒')[0].autoParams()

        if code_re.match(message) and self.checkValidCode(message, openId):
            return WeiXinAutoResponse.objects.get_or_create(message=u'校验成功提示')[0].autoParams()

        if message == '0' and self._wx_user.isValid():
            return self.genTextRespJson(u'您已成功绑定手机：\n[q] 取消绑定 \n*取消绑定后部分功能失效')

        fullmatch_responses = WeiXinAutoResponse.objects.FullMatch.filter(message=message)
        for resp in fullmatch_responses:
            if message == resp.message.strip():
                return resp.autoParams()

        fuzzymatch_responses = WeiXinAutoResponse.objects.FuzzyMatch.filter(message__icontains=message)
        for resp in fuzzymatch_responses:
            if message.rfind(resp.message.strip()) > -1:
                return resp.autoParams()

        return WeiXinAutoResponse.respDKF()

    def getTrade2BuyerStatus(self, status, sys_status):

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

    def genTextRespJson(self, text):
        return {'MsgType': WeiXinAutoResponse.WX_TEXT,
                'Content': text}

    def sendValidCode(self, mobile, validCode, title=u'微信手机验证'):

        from shopapp.smsmgr import sendMessage

        wx_resp = WeiXinAutoResponse.objects.get_or_create(message='SJYZM')[0]
        msgTemplate = wx_resp.content

        return sendMessage(mobile, title, msgTemplate % validCode)

    def formatJsonToPrettyString(self, jsonContent):
        assert type(jsonContent) in (list, tuple)

        jsonStrArray = []
        for a in jsonContent:
            if type(a[1]) not in (list, tuple):
                jsonStrArray.extend([a[0], '\n\t', a[1], '\n'])
                continue
            jsonStrArray.extend([a[0], '\n'])
            for l in a[1]:
                if type(l) not in (tuple, list):
                    jsonStrArray.extend(['\t', l, '\n'])
                    continue
                jsonStrArray.extend([l[0], '\n\t', l[1], '\n'])
        return ''.join(jsonStrArray)

    def getLatestTradeByMobile(self, mobile):

        latest_trades = MergeTrade.objects.filter(
            receiver_mobile=mobile) \
            .order_by('-pay_time')
        if latest_trades.count() == 0:
            raise MessageException(u'你还没有交易记录哦')
        return latest_trades[0]

    def getTradeMessageByMobile(self, mobile):

        trade_array = []

        trade = self.getLatestTradeByMobile(mobile)

        trade_array.append((u'昵称', trade.buyer_nick))
        trade_array.append((u'成交时间', trade.pay_time and format_datetime(trade.pay_time)))
        trade_array.append((u'订单状态', self.getTrade2BuyerStatus(trade.status, trade.sys_status)))
        orders = []
        for order in trade.merge_orders.filter(sys_status=pcfg.IN_EFFECT):
            orders.append(order.getSimpleName())
        trade_array.append((u'订单详细', orders))

        return self.genTextRespJson(self.formatJsonToPrettyString(trade_array))

    def getLogisticMessageByMobile(self, mobile):

        trade = self.getLatestTradeByMobile(mobile)
        if not trade.out_sid or not trade.logistics_company:
            raise MessageException(u'亲请稍安勿燥，宝贝正在准备出库中...')

        trade_traces = getLogisticTrace(trade.out_sid,
                                        trade.logistics_company.code.split('_')[0])

        return self.genTextRespJson(self.formatJsonToPrettyString(trade_traces))

    def getReferalProgramWelcomeMessage(self, mobile):
        msg = "把优尼世界推荐给您的朋友，你们双方都将有机会获得额外的返利。\n\n请输入您朋友的姓氏和她的手机号,用#号连接：\n(例如：李#13801235666)"
        return self.genTextRespJson(msg)

    def addReferal(self, referal_from_mobile, referal_to_mobile, referal_to_lastname):

        from shopback.users.models import Customer
        from shopapp.weixin.models import ReferalRelationship
        user_exists_num = Customer.objects.filter(mobile=referal_to_mobile).count()

        if user_exists_num > 0:
            return False

        Customer.objects.create(mobile=referal_to_mobile)

        ReferalRelationship.objects.create(
            referal_from_mobile=referal_from_mobile,
            referal_to_mobile=referal_to_mobile,
            referal_to_lastname=referal_to_lastname
        )

        return True

    def sendFaqsList(self, wx_user):
        # send the faqs list
        faq_responses = WeiXinAutoResponse.objects.filter(rtype=WeiXinAutoResponse.WX_NEWS, message='FAQS')
        if faq_responses.count() > 0:
            faq = faq_responses[0]
            return faq.respNews()
        return MessageException(u'服务器正在忙碌哦！\n 请稍后访问哦')

    def handleEvent(self, eventKey, openId, eventType=WeiXinAutoResponse.WX_EVENT_CLICK):
        if self._wx_user.isNone():
            raise MessageException(u'用户信息获取异常')

        eventKey = eventKey.upper()

        if eventKey in ('Q', 'W', 'E', 'R', 'Z') and not self._wx_user.isValid():
            raise MessageException(u'你还没有绑定手机哦!\n请输入手机号:')

        if eventKey == "Q":
            self._wx_user.isvalid = False
            self._wx_user.save()
            raise MessageException(u'您的手机已取消绑定 \n重新绑定请输入数字[0]:')

        elif eventKey == "W":
            return self.getTradeMessageByMobile(self._wx_user.mobile)

        elif eventKey == "E":
            return self.getLogisticMessageByMobile(self._wx_user.mobile)

        elif eventKey == "Z":
            return self.getReferalProgramWelcomeMessage(self._wx_user.mobile)

        elif eventKey == 'Y':
            return WeiXinAutoResponse.respDKF()

        elif eventKey == 'N':
            raise MessageException(u'[OK]期待下次为您服务[愉快]')

        elif eventKey == 'FAQS':
            return self.sendFaqsList(self._wx_user)

        if eventType == WeiXinAutoResponse.WX_EVENT_SUBSCRIBE:
            self._wx_user.doSubscribe(eventKey.rfind('_') > -1 and eventKey.split('_')[1] or '')
            return WeiXinAutoResponse.respDefault()

        elif eventType == WeiXinAutoResponse.WX_EVENT_UNSUBSCRIBE:
            self._wx_user.unSubscribe()
            return WeiXinAutoResponse.respEmptyString()

        elif eventType in (WeiXinAutoResponse.WX_EVENT_KF_CLOSE_SESSION,
                           WeiXinAutoResponse.WX_EVENT_KF_CREATE_SESSION):
            return WeiXinAutoResponse.respEmptyString()

        return self.getResponseByBestMatch(eventKey, openId)

    def handleMerchantOrder(self, user_id, order_id, order_status=2, product_id='', sku_info=''):

        from shopback.trades.service import TradeService

        TradeService.createTrade(user_id, order_id, pcfg.WX_TYPE)

        return self.genTextRespJson(u'您的订单(%s)已收到,我们会尽快将宝贝寄给您。[玫瑰]' % order_id)

    def handleSaleAction(self, user_id, pictures, attach_files=[]):

        pic_count = int(pictures['Count'])
        #
        #        from shopapp.weixin_sales.service import WeixinSaleService
        #
        #        WeixinSaleService(self._wx_user).uploadPicture(pictures,attach_files=attach_files)

        return self.genTextRespJson(u'[愉快]图片上传成功')

    def handleRequest(self, params):

        MsgId = params.get('MsgId', None)
        ret_params = {'ToUserName': params['FromUserName'],
                      'FromUserName': params['ToUserName'],
                      'CreateTime': int(time.time())}
        if MsgId and not cache.add(MsgId, True, WX_MESSAGE_TIMEOUT):
            ret_params.update(WeiXinAutoResponse.respDKF())
            return ret_params

        openId = params['FromUserName']
        msgtype = params['MsgType']
        self.setOpenId(openId)
        try:
            if msgtype == WeiXinAutoResponse.WX_EVENT:
                eventType = params['Event']
                if eventType == WeiXinAutoResponse.WX_EVENT_ORDER:
                    ret_params.update(self.handleMerchantOrder(params['ToUserName'],
                                                               params['OrderId'],
                                                               params['OrderStatus'],
                                                               params['ProductId'],
                                                               params['SkuInfo']))
                elif eventType == WeiXinAutoResponse.WX_EVENT_LOCATION:
                    ret_params.update(self.genTextRespJson(
                        u'你的地理位置（%s,%s）.' %
                        (params['Latitude'], params['Longitude'])))
                elif eventType in (WeiXinAutoResponse.WX_EVENT_PIC_SYSPHOTO,
                                   WeiXinAutoResponse.WX_EVENT_PIC_ALBUM,
                                   WeiXinAutoResponse.WX_EVENT_PIC_WEIXIN):
                    ret_params.update(self.handleSaleAction(openId,
                                                            params['SendPicsInfo']))
                else:
                    eventKey = params.get('EventKey', '')
                    ret_params.update(self.handleEvent(eventKey and eventKey.upper() or '',
                                                       openId, eventType=eventType))
                return ret_params

            matchMsg = ''
            if msgtype == WeiXinAutoResponse.WX_TEXT:
                matchMsg = params['Content'] or ''
                if event_re.match(matchMsg):
                    ret_params.update(self.handleEvent(matchMsg.upper(), openId))
                    return ret_params

            elif msgtype == WeiXinAutoResponse.WX_IMAGE:
                # 保存微信用户上传图片
                # from shopapp.weixin_sales.service import WeixinSaleService
                # WeixinSaleService(self._wx_user).downloadPicture(params['MediaId'])
                ret_params.update(WeiXinAutoResponse.respDKF())
                return ret_params

            elif msgtype == WeiXinAutoResponse.WX_VOICE:
                matchMsg = u'语音'
            elif msgtype == WeiXinAutoResponse.WX_VIDEO:
                matchMsg = u'视频'
            elif msgtype == WeiXinAutoResponse.WX_LOCATION:
                matchMsg = u'位置'
            else:
                matchMsg = u'链接'
            resp = self.getResponseByBestMatch(matchMsg.strip(), openId)
            ret_params.update(resp)
        except MessageException, exc:
            ret_params.update(self.genTextRespJson(exc.message))
        except Exception, exc:
            logger.error(u'微信请求异常:%s' % exc.message, exc_info=True)
            ret_params.update(self.genTextRespJson(u'不好了，小优尼闹情绪不想干活了！[撇嘴]'))
        return ret_params


from .models import WXProductSku, MIAOSHA_SELLER_ID


class WxShopService(LocalService):
    order = None
    wx_api = None

    def __init__(self, t):
        assert t not in ('', None)

        if isinstance(t, WXOrder):
            self.order = t
        else:
            self.order = WXOrder.objects.get(order_id=t)

        self.wx_api = WxShopService.getWXApiInstance()

    @classmethod
    def getWXApiInstance(cls):

        return WeiXinAPI()

    @classmethod
    def createTradeByDict(cls, user_id, order_dict):

        order, state = WXOrder.objects.get_or_create(order_id=order_dict['order_id'],
                                                     seller_id=user_id)

        for k, v in order_dict.iteritems():
            hasattr(order, k) and setattr(order, k, v)

        order.buyer_nick = replace_utf8mb4(order_dict['buyer_nick']).strip()
        order.order_create_time = datetime.datetime.fromtimestamp(
            int(order_dict['order_create_time']))

        order.save()

        return order

    @classmethod
    def createTrade(cls, user_id, tid, *args, **kwargs):

        order_id = tid
        wx_api = cls.getWXApiInstance()

        order_dict = wx_api.getOrderById(order_id)

        order = cls.createTradeByDict(user_id, order_dict)

        return order

    @classmethod
    def createMergeOrder(cls, merge_trade, order, *args, **kwargs):

        merge_order, state = MergeOrder.objects.get_or_create(oid=order.order_id,
                                                              merge_trade=merge_trade)
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
            wx_skus = WXProductSku.objects.filter(sku_id=order.product_sku, product=wx_product)
            outer_id, outer_sku_id = '', ''
            if wx_skus.count() > 0:
                outer_id = wx_skus[0].outer_id
                outer_sku_id = wx_skus[0].outer_sku_id

            merge_order.payment = order.order_total_price / 100.0
            merge_order.created = order.order_create_time
            merge_order.pay_time = order.order_create_time
            merge_order.num = order.product_count
            merge_order.title = order.product_name
            merge_order.pic_path = order.product_img
            merge_order.outer_id = outer_id
            merge_order.outer_sku_id = outer_sku_id

        merge_order.refund_status = refund_status
        merge_order.status = WXOrder.mapOrderStatus(order.order_status)
        merge_order.sys_status = sys_status
        merge_order.save()
        return merge_order

    @classmethod
    def getOrCreateSeller(cls, trade):
        wx_product = WXProduct.objects.getOrCreate(trade.product_id)
        product_name = wx_product.product_name

        seller_id = trade.seller_id
        if product_name.find(u'秒杀') >= 0:
            ###需要创建wxmiaosha 该买家才能正常工作
            seller_id = MIAOSHA_SELLER_ID
            if trade.buyer_nick.find(u'[秒杀]') < 0:
                trade.buyer_nick = u'[秒杀]' + trade.buyer_nick
        seller = User.getOrCreateSeller(seller_id, seller_type=User.SHOP_TYPE_WX)
        return seller

    @classmethod
    def createMergeTrade(cls, trade, *args, **kwargs):

        user = cls.getOrCreateSeller(trade)
        merge_trade, state = MergeTrade.objects.get_or_create(user=user,
                                                              tid=trade.order_id)

        update_fields = ['buyer_nick', 'created', 'pay_time', 'modified', 'status']

        merge_trade.buyer_nick = trade.buyer_nick or trade.receiver_name
        merge_trade.created = trade.order_create_time
        merge_trade.modified = trade.order_create_time
        merge_trade.pay_time = trade.order_create_time
        merge_trade.status = WXOrder.mapTradeStatus(trade.order_status)

        update_address = False
        if not merge_trade.receiver_name and trade.receiver_name:
            update_address = True
            merge_trade.receiver_name = trade.receiver_name
            merge_trade.receiver_state = trade.receiver_province
            merge_trade.receiver_city = trade.receiver_city
            merge_trade.receiver_district = trade.receiver_zone
            merge_trade.receiver_address = trade.receiver_address
            merge_trade.receiver_mobile = trade.receiver_mobile
            merge_trade.receiver_phone = trade.receiver_phone

            address_fields = ['receiver_name', 'receiver_state', 'receiver_district',
                              'receiver_city', 'receiver_address',
                              'receiver_mobile', 'receiver_phone']

            update_fields.extend(address_fields)

        merge_trade.payment = (merge_trade.payment or
                               round(trade.order_total_price / 100.0, 2))
        merge_trade.total_fee = (merge_trade.total_fee or
                                 round(trade.product_price / 100.0, 2) * trade.product_count)
        merge_trade.post_fee = (merge_trade.post_fee or
                                round(trade.order_express_price / 100.0, 2))

        merge_trade.trade_from = MergeTrade.trade_from.WAP
        merge_trade.shipping_type = pcfg.EXPRESS_SHIPPING_TYPE
        merge_trade.type = pcfg.WX_TYPE

        update_model_fields(merge_trade, update_fields=update_fields
                                                       + ['shipping_type', 'type', 'payment',
                                                          'total_fee', 'post_fee', 'trade_from'])

        cls.createMergeOrder(merge_trade, trade)

        _params = {'origin_trade': trade,
                   'update_address': (update_address and
                                      merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS),
                   'first_pay_load': (merge_trade.sys_status == pcfg.EMPTY_STATUS and
                                      merge_trade.status == pcfg.WAIT_SELLER_SEND_GOODS)}
        _params.update(kwargs)

        if _params.get('first_pay_load'):
            trade.confirm_payment()

        trade_handler.proccess(merge_trade, *args, **_params)

        return merge_trade

    def payTrade(self, *args, **kwargs):

        wxorder = self.__class__.createTrade(self.order.seller_id,
                                             self.order.order_id)

        merge_trade = WxShopService.createMergeTrade(wxorder, *args, **kwargs)

        return merge_trade

    def sendTrade(self, company_code=None, out_sid=None, retry_times=3, *args, **kwargs):

        try:
            wx_logistic = WXLogistic.objects.get(origin_code__icontains=company_code.split('_')[0])
        except:
            is_others = 1
            lg_code = company_code

        else:
            is_others = 0
            lg_code = wx_logistic.company_code

        need_delivery = 1
        if company_code == LogisticsCompany.NOPOST:
            lg_code = ''
            out_sid = ''
            need_delivery = 0
        try:
            self.wx_api.deliveryOrder(self.order.order_id,
                                      lg_code,
                                      out_sid,
                                      need_delivery=need_delivery,
                                      is_others=is_others)
        except Exception, exc:
            logger.error(u'微信发货失败:%s' % exc.message, exc_info=True)
            raise exc

        else:
            self.order.order_status = WXOrder.WX_WAIT_CONFIRM
            self.order.delivery_id = out_sid
            self.order.delivery_company = lg_code
            self.order.save()
