#-*- encoding:utf-8 -*-
import re
import time
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from shopapp.weixin.service import WeixinUserService
from models import WeiXinUser,ReferalRelationship,ReferalSummary,WXOrder,Refund

from shopback.trades.models import MergeTrade

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


from urllib import urlopen



def get_user_openid(code, appid, secret):
    url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code'
    get_openid_url = url % (appid, secret, code)
    r = urlopen(get_openid_url).read()
    r = json.loads(r)
    return r.get('openid')


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



from django.shortcuts import render_to_response
from django.template import RequestContext


class RequestCodeView(View):
    def get(self, request, *args, **kwargs):
        mobile = kwargs.get('mobile',0)
        if len(mobile) != 11:
            response = {"code":"bad", "message":"wrong phone number"}
            return HttpResponse(json.dumps(response),mimetype='application/json')

        content = request.REQUEST

        code = content.get('code')

        APPID = 'wxc2848fa1e1aa94b5'
        SECRET = 'eb3bfe8e9a36a61176fa5cafe341c81f'

        ## if user refresh page, we can get user_openid from cookie
        user_openid = request.COOKIES.get('openid')

        if user_openid == 'None' or user_openid == None:
            user_openid = get_user_openid(code, APPID, SECRET)


        wx_user_service = WeixinUserService(openId=user_openid)
        code = wx_user_service.genValidCode()

        # we have to write code into user's profile
        wx_user_service.sendValidCode(mobile, code)
        wx_user = wx_user_service._wx_user
        wx_user.mobile    = mobile
        wx_user.isvalid   = False
        wx_user.validcode = code
        wx_user.valid_count += 1
        wx_user.code_time = datetime.datetime.now()
        wx_user.save()

        
        response = {"code":"good", "message":"code has been sent"}
        return HttpResponse(json.dumps(response),mimetype='application/json')

class VerifyCodeView(View):
    def get(self, request, *args, **kwargs):
        verifycode = kwargs.get('verifycode',0)
        if len(verifycode) != 6:
            response = {"code":"bad", "message":"wrong verification code"}
            return HttpResponse(json.dumps(response),mimetype='application/json')

        ## if user refresh page, we can get user_openid from cookie
        user_openid = request.COOKIES.get('openid')

        if user_openid == 'None' or user_openid == None:
            APPID = 'wxc2848fa1e1aa94b5'
            SECRET = 'eb3bfe8e9a36a61176fa5cafe341c81f'
            user_openid = get_user_openid(code, APPID, SECRET)

        wx_user_service = WeixinUserService(openId=user_openid)
        wx_user = wx_user_service._wx_user
        if not wx_user.validcode or wx_user.validcode != verifycode:
            response = {"code":"bad", "message":"invalid code"}
        else:    
            wx_user.isvalid = True
            wx_user.save()
            response = {"code":"good", "message":"code has been verified"}
            
        return HttpResponse(json.dumps(response),mimetype='application/json')
        
    
class OrderInfoView(View):

    def get(self, request):
        content = request.REQUEST

        code = content.get('code')

        APPID = 'wxc2848fa1e1aa94b5'
        SECRET = 'eb3bfe8e9a36a61176fa5cafe341c81f'

        ## if user refresh page, we can get user_openid from cookie
        user_openid = request.COOKIES.get('openid')

        if user_openid == 'None' or user_openid == None:
            user_openid = get_user_openid(code, APPID, SECRET)

        
        weixin_user_service = WeixinUserService(user_openid)
        wx_user = weixin_user_service._wx_user
        
        if wx_user.isValid() == False:
            response = render_to_response('weixin/remind.html', context_instance=RequestContext(request))
            response.set_cookie("openid",user_openid)
            return response
            

        latest_trades = MergeTrade.objects.filter(receiver_mobile=wx_user.mobile).order_by('-pay_time')
        
        if latest_trades.count() == 0:
            wx_trades = WXOrder.objects.filter(buyer_openid=user_openid).order_by('-order_create_time') 
            if wx_trades.count() == 0:
                response = render_to_response('weixin/noorderinfo.html', 
                                      context_instance=RequestContext(request))
                response.set_cookie("openid",user_openid)
                return response
            
            order_id = wx_trades[0].order_id
            latest_trades = MergeTrade.objects.filter(tid=order_id).order_by('-pay_time')
            
        from shopback import paramconfig as pcfg
        
        trade = latest_trades[0]
        
        data = {}
        data["tradeid"] = trade.id
        data["platform"] = trade.user
        data["paytime"] = trade.pay_time
        orders = []
        for order in trade.merge_orders.filter(sys_status=pcfg.IN_EFFECT):
            s = order.getImgSimpleNameAndPrice()
            print 's',s
            orders.append(s)
        data["orders"] = orders
        data["ordernum"] = trade.order_num
        data["payment"] = trade.payment
        data["receiver_name"] = trade.receiver_name
        data["receiver_mobile"] = trade.receiver_mobile
        data["address"] = ','.join([trade.receiver_state, trade.receiver_city, trade.receiver_district, trade.receiver_address])
        
        from shopback.logistics import getLogisticTrace
        shipping_traces = []
        try:
            shipping_traces = getLogisticTrace(trade.out_sid, trade.logistics_company.code.split('_')[0])
        except:
            shipping_traces = [("Sorry, 暂时无法查询到快递信息", "请尝试其他途径查询")]

        
        refund = None
        refund_list = Refund.objects.filter(trade_id=trade.id)
        if refund_list.count() > 0:
            refund = refund_list[0]
        response = render_to_response('weixin/orderinfo.html', 
                                      {'tradedata':data, "traces":shipping_traces, "refund": refund},
                                      context_instance=RequestContext(request))
        response.set_cookie("openid",user_openid)
        return response


from datetime import date

class BabyInfoView(View):

    def get(self, request):
        content = request.REQUEST

        code = content.get('code')

        APPID = 'wxc2848fa1e1aa94b5'
        SECRET = 'eb3bfe8e9a36a61176fa5cafe341c81f'

        ## if user refresh page, we can get user_openid from cookie
        user_openid = request.COOKIES.get('openid')

        if user_openid == 'None' or user_openid == None:
            user_openid = get_user_openid(code, APPID, SECRET)

        wx_user_service = WeixinUserService(user_openid)
        wx_user = wx_user_service._wx_user
        
        years = [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015]
        months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        response = render_to_response('weixin/babyinfo.html', 
                                      {'user':wx_user, 'years': years, 'months': months},
                                      context_instance=RequestContext(request))
        response.set_cookie("openid",user_openid)
        return response
        
    def post(self, request, *args, **kwargs):
        content = request.REQUEST
        year = content.get("year")
        month  = content.get("month")
        sex  = content.get("sex")

        receiver_name = content.get("receiver_name")
        province = content.get("province")
        city = content.get("city")
        streetaddr = content.get("streetaddr")

        user_openid = request.COOKIES.get('openid')
        code = content.get("code")
        if user_openid == 'None' or user_openid == None:
            APPID = 'wxc2848fa1e1aa94b5'
            SECRET = 'eb3bfe8e9a36a61176fa5cafe341c81f'
            user_openid = get_user_openid(code, APPID, SECRET)

        wx_user_service = WeixinUserService(openId=user_openid)
        wx_user = wx_user_service._wx_user

        wx_user.birth_year = int(year)
        wx_user.birth_month = int(month)
        wx_user.baby_sex = sex
        wx_user.receiver_name = receiver_name
        wx_user.province = province
        wx_user.city = city
        wx_user.address = streetaddr

        
        wx_user.save()
        
        response = {"birth_year":wx_user.birth_year, "birth_month":wx_user.birth_month,
                    "sex":wx_user.baby_sex, "receiver_name":wx_user.receiver_name,
                    "province":wx_user.province,"city":wx_user.city,
                    "streetaddr":wx_user.address, "code":"ok", "message":"saved"}

        return HttpResponse(json.dumps(response),mimetype='application/json')

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
        
        


class ReferalView(View):

    def get(self, request):
        content = request.REQUEST

        code = content.get('code')

        APPID = 'wxc2848fa1e1aa94b5'
        SECRET = 'eb3bfe8e9a36a61176fa5cafe341c81f'

        ## if user refresh page, we can get user_openid from cookie
        user_openid = request.COOKIES.get('openid')

        if user_openid == 'None' or user_openid == None:
            user_openid = get_user_openid(code, APPID, SECRET)
            
        direct_referal_count = 0
        indirect_referal_count = 0
        referal_bonus = 0.00
        
        rs = ReferalSummary.objects.filter(user_openid=user_openid)

        if rs.count() > 0:
            direct_referal_count = rs[0].direct_referal_count
            indirect_referal_count = rs[0].indirect_referal_count
            referal_bonus = rs[0].total_confirmed_value * 0.01
        
        
        response = render_to_response('weixin/referal.html', 
                                  {'openid':user_openid, 
                                   'direct_referal_count':direct_referal_count, 
                                   'indirect_referal_count':indirect_referal_count, 
                                   'referal_bonus':referal_bonus}, 
                                  context_instance=RequestContext(request))
        response.set_cookie("openid",user_openid)
        return response


class RefundSubmitView(View):
    def post(self, request):
        content = request.REQUEST
        tradeid = content.get("tradeid")
        refundtype = content.get("refund_type")
        vipcode = content.get("vipcode")
        
        obj = Refund.objects.filter(trade_id=tradeid)
        if obj.count() < 1:
            if refundtype == "0":
                obj = Refund.objects.create(trade_id=int(tradeid),refund_type=int(refundtype))
            else:
                obj = Refund.objects.create(trade_id=int(tradeid),refund_type=int(refundtype),vip_code=vipcode)
        else:
            obj = obj[0]
        response = render_to_response('weixin/refundresponse.html', {"refund":obj},
                                      context_instance=RequestContext(request))
        return response

        

class RefundReviewView(View):
    def get(self, request):
        
        content = request.REQUEST
        refund_status = int(content.get("status", "0"))
        
        refundlist = Refund.objects.filter(refund_status=refund_status).order_by('created')
        
        first_refund, first_trade = None,None
        if refundlist.count() > 0:
            first_refund = refundlist[0]
            first_refund.pay_amount = first_refund.pay_amount * 0.01
            trade_id = first_refund.trade_id
            mergetrades = MergeTrade.objects.filter(id=int(trade_id))
            if mergetrades.count() > 0:
                first_trade = mergetrades[0]
                
        
        response = render_to_response('weixin/refundreview.html', 
                                      {"refundlist":refundlist, "first_refund":first_refund, "first_trade": first_trade, "refund_status":refund_status},
                                      context_instance=RequestContext(request))
        return response

    def post(self, request):
        content = request.REQUEST

        refund_status = int(content.get("refund_status"))
        refund_id = int(content.get("refund_id"))

        if refund_status == 1:
            pay_note = content.get("pay_note")            
            action = int(content.get("action"))            

            if not action in (2,3):
                response = {"code":"bad", "message":"wrong action"}
                return HttpResponse(json.dumps(response),mimetype='application/json')

            Refund.objects.filter(pk=refund_id).update(pay_note=pay_note,refund_status=action)

        if refund_status == 0:
            pay_type = int(content.get("pay_type"))
            pay_amount = int(content.get("pay_amount"))
            review_note = content.get("review_note",)
            action = int(content.get("action"))

            if not action in (1,2):
                response = {"code":"bad", "message":"wrong action"}
                return HttpResponse(json.dumps(response),mimetype='application/json')

            Refund.objects.filter(pk=refund_id).update(pay_type=pay_type,pay_amount=pay_amount,review_note=review_note,refund_status=action)
        
        refunds = Refund.objects.filter(pk__gt=refund_id).filter(refund_status=refund_status).order_by('pk')[0:1]
        next_trade,next_refund = None,None
        if refunds.count() > 0:
            next_refund = refunds[0]
            next_refund.pay_amount = next_refund.pay_amount * 0.01
            mergetrades = MergeTrade.objects.filter(id=next_refund.trade_id)
            if mergetrades.count() > 0:
                next_trade = mergetrades[0]
            
        html = 'weixin/refundreviewblock.html'
        if refund_status == 1:
            html = 'weixin/finalizeblock.html'
        response = render_to_response(html, {"first_refund":next_refund, "first_trade": next_trade},
                                      context_instance=RequestContext(request))
        return response
    

        

class TestView(View):
    def get(self, request):
        response = render_to_response('weixin/orderinfo.html', 
                                      context_instance=RequestContext(request))
        return response
        
