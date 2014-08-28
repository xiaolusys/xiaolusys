#-*- encoding:utf-8 -*-
import re
import time
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from shopapp.weixin.service import *
from .models import (WeiXinUser,
                     ReferalRelationship,
                     ReferalSummary,
                     ReferalBonusRecord,
                     WXOrder,
                     Refund,
                     FreeSample, 
                     SampleSku, 
                     SampleOrder,
                     VipCode,
                     Coupon,
                     CouponClick,
                     Survey)

from shopback.trades.models import MergeTrade
from shopback import paramconfig as pcfg

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
    """ 
    <xml>
    <OpenId><![CDATA[oMt59uE55lLOV2KS6vYZ_d0dOl5c]]></OpenId>
    <AppId><![CDATA[wxc2848fa1e1aa94b5]]></AppId>
    <TimeStamp>1406598314</TimeStamp>
    <MsgType><![CDATA[request]]></MsgType>
    <FeedBackId>13294025981597859672</FeedBackId>
    <TransId><![CDATA[1219468801201407253242545244]]></TransId>
    <Reason><![CDATA[\u9000]]></Reason>
    <Solution><![CDATA[\u9000\u6b3e\uff0c\u5e76\u4e0d\u9000\u8d27]]></Solution>
    <ExtInfo><![CDATA[ ]]></ExtInfo>
    <AppSignature><![CDATA[88518237d2e188a367880784ee209d278190a02d]]></AppSignature>
    <SignMethod><![CDATA[sha1]]></SignMethod>
    </xml>
    """
    params = parseXML2Param(request.body)
    
    logger.error('WEIXIN FEEDBACK_URL:%s'%str(request.REQUEST))
    return HttpResponse('success')

@csrf_exempt
def warn(request):
    """
    <xml>
        <AppId><![CDATA[wxf8b4f85f3a794e77]]></AppId>
        <ErrorType>1001</ErrorType>
        <Description><![CDATA[错误描述]]></Description>
        <AlarmContent><![CDATA[错误详情]]></AlarmContent>
        <TimeStamp>1393860740</TimeStamp>
        <AppSignature><![CDATA[11111]]></AppSignature>
        <SignMethod><![CDATA[sha1]]></SignMethod>
    </xml>
    """
    params = parseXML2Param(request.body)
    
    mail_logger = logging.getLogger('mail.handler')
    mail_logger.info(u'微店警告:(%s,%s,%s)'%(params['ErrorType'],
                                      params['Description'],
                                      params['AlarmContent']))
    return HttpResponse('success')


from urllib import urlopen



def get_user_openid(request, code):
    appid = settings.WEIXIN_APPID
    secret = settings.WEIXIN_SECRET
    url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code'
    get_openid_url = url % (appid, secret, code)
    r = urlopen(get_openid_url).read()
    r = json.loads(r)

    if r.has_key("errcode"):
        openid = request.COOKIES.get('openid')
        return openid 

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
        
        params   = parseXML2Param(content)
        
        ret_params = wx_service.handleRequest(params)
       
        response = formatParam2XML(ret_params)
        
        return HttpResponse(response,mimetype="text/xml")



from django.shortcuts import render_to_response
from django.template import RequestContext


class RequestCodeView(View):
    def get(self, request, *args, **kwargs):
        content = request.REQUEST
        mobile = content.get('mobile','0')
        openid = content.get('openid',None)
        if len(mobile) != 11:
            response = {"code":"bad", "message":"wrong phone number"}
            return HttpResponse(json.dumps(response),mimetype='application/json')
        
        wx_users = WeiXinUser.objects.filter(mobile=mobile,isvalid=True)
        if wx_users.count() > 0:
            response = {"code":"dup", "message":"duplication phone"}
            return HttpResponse(json.dumps(response),mimetype='application/json')
        
        wx_user_service = WeixinUserService(openId=openid)
        if wx_user_service._wx_user.isNone():
            response = {"code":"anony", "message":"anonymous user"}
            return HttpResponse(json.dumps(response),mimetype='application/json')

        code = wx_user_service.genValidCode()
        wx_user = wx_user_service._wx_user
        
        if wx_user.valid_count >= 5:
            response = {"code":"locked", "message":"limit reached, please contact us"}
            return HttpResponse(json.dumps(response),mimetype='application/json')
        
        if wx_user.valid_count > 0:
            prev_time = wx_user.code_time
            diff_time = datetime.datetime.now() - wx_user.code_time
            if diff_time.seconds < 60:
                response = {"code":"wait", "message":"wait 60s before requesting new code"}
                return HttpResponse(json.dumps(response),mimetype='application/json')
                
        # we have to write code into user's profile
        wx_user_service.sendValidCode(mobile, code)
        wx_user = wx_user_service._wx_user
        wx_user.vmobile   = mobile
        wx_user.isvalid   = False
        wx_user.validcode = code
        wx_user.valid_count += 1
        wx_user.code_time = datetime.datetime.now()
        wx_user.save()
        
        response = {"code":"good", "message":"code has been sent"}
        return HttpResponse(json.dumps(response),mimetype='application/json')


class VerifyCodeView(View):
    def get(self, request):
        content = request.REQUEST
        verifycode = content.get('verifycode','0')
        openid = content.get('openid',None)
        if len(verifycode) not in (6, 7):
            response = {"code":"bad", "message":"wrong verification code"}
            return HttpResponse(json.dumps(response),mimetype='application/json')

        wx_user, state = WeiXinUser.objects.get_or_create(openid=openid)
        if not wx_user.validcode or wx_user.validcode != verifycode:
            response = {"code":"bad", "message":"invalid code"}
        else:    
            wx_user.mobile = wx_user.vmobile
            wx_user.isvalid = True
            wx_user.save()
            
            VipCode.objects.genVipCodeByWXUser(wx_user)
            
            response = {"code":"good", "message":"code has been verified"}
            
        return HttpResponse(json.dumps(response),mimetype='application/json')
        
    
class OrderInfoView(View):
    def get(self, request):
        content = request.REQUEST
        code = content.get('code',None)
        user_openid = get_user_openid(request, code)
        
        weixin_user_service = WeixinUserService(user_openid)
        wx_user = weixin_user_service._wx_user
        
        title = u'订单查询'
        if wx_user.isValid() == False:
            response = render_to_response('weixin/remind.html', 
                                          {"title":title, "openid":user_openid}, 
                                          context_instance=RequestContext(request))
            response.set_cookie("openid",user_openid)
            return response
            
        status = [pcfg.WAIT_SELLER_SEND_GOODS,pcfg.WAIT_BUYER_CONFIRM_GOODS, pcfg.TRADE_FINISHED]
        latest_trades = MergeTrade.objects.filter(receiver_mobile=wx_user.mobile).filter(status__in=status).order_by('-pay_time')
        
        if latest_trades.count() == 0:
            wx_trades = WXOrder.objects.filter(buyer_openid=user_openid).order_by('-order_create_time') 
            if wx_trades.count() == 0:
                response = render_to_response('weixin/noorderinfo.html', 
                                      context_instance=RequestContext(request))
                response.set_cookie("openid",user_openid)
                return response
            
            order_id = wx_trades[0].order_id
            latest_trades = MergeTrade.objects.filter(tid=order_id).order_by('-pay_time')
            

        
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
        
        passed = False
        sample_orders = SampleOrder.objects.filter(user_openid=user_openid).filter(status__gt=0).filter(status__lt=7)
        if sample_orders.count() > 0:
            passed = True
        
        response = render_to_response('weixin/orderinfo.html', 
                                      {'tradedata':data, "traces":shipping_traces, 
                                       "refund": refund, "passed":passed, "openid":user_openid },
                                      context_instance=RequestContext(request))
        response.set_cookie("openid",user_openid)
        return response


from datetime import date

class BabyInfoView(View):

    def get(self, request):
        content = request.REQUEST
        code = content.get('code')

        if code == None or code == "None":
            response = {"msg":u'请从[优尼世界]微信打开此页面！'}
            return HttpResponse(json.dumps(response),mimetype='application/json')
        
        openid = get_user_openid(request, code)
            
        wx_user_service = WeixinUserService(openid)
        wx_user = wx_user_service._wx_user
        
        samples = FreeSample.objects.filter(expiry__gt=datetime.datetime.now())
        
        years = [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015]
        months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        response = render_to_response('weixin/babyinfo.html', 
                                      {'user':wx_user, 'years': years, 
                                       'months': months, 'openid':openid,
                                       'sample_count':samples.count()},
                                      context_instance=RequestContext(request))
        response.set_cookie("openid",openid)
        return response
        
    def post(self, request):
        content = request.REQUEST
        year = content.get("year")
        month  = content.get("month")
        sex  = content.get("sex")

        receiver_name = content.get("receiver_name")
        province = content.get("province")
        city = content.get("city")
        streetaddr = content.get("streetaddr")
        openid = content.get('openid')

        wx_user_service = WeixinUserService(openId=openid)
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
        user_openid = get_user_openid(request, code)
            
        referal_bonus = 0.00
        vipcode = ""
        users = WeiXinUser.objects.filter(openid=user_openid)
        if users.count() > 0:
            vipcodes = users[0].vipcodes.all()
            if vipcodes.count() > 0:
                vipcode = vipcodes[0].code
        
        referal_count = SampleOrder.objects.filter(vipcode=vipcode).count()
        
        coupon = Coupon.objects.get(pk=1)
        
        couponclicks = CouponClick.objects.filter(vipcode=vipcode)
        coupon_click_count = couponclicks.count()

        referal_mobiles = set()
        mobile2openid = {}

        referal_users = WeiXinUser.objects.filter(referal_from_openid=user_openid)
        for user in referal_users:
            referal_mobiles.add(user.mobile)
            mobile2openid[str(user.mobile)] = user.openid

        for coupon_click in couponclicks:
            referal_mobiles.add(coupon_click.wx_user.mobile)
            mobile2openid[str(coupon_click.wx_user.mobile)]=coupon_click.wx_user.openid

        payment = 0
        
        effect_mobiles = set()
        order_status = [pcfg.WAIT_SELLER_SEND_GOODS,pcfg.WAIT_BUYER_CONFIRM_GOODS]
        effect_date = datetime.datetime(2014,8,3)
        for mobile in referal_mobiles:
            trades = MergeTrade.objects.filter(receiver_mobile=mobile).filter(status__in=order_status).filter(created__gt=effect_date)
            for trade in trades:
                payment += trade.payment
                effect_mobiles.add(mobile)

            confirmed_trades = MergeTrade.objects.filter(receiver_mobile=mobile).filter(status=pcfg.TRADE_FINISHED).filter(created__gt=effect_date)
            for trade in confirmed_trades:
                records = ReferalBonusRecord.objects.filter(trade_id=trade.id)
                if records.count() < 1:
                    if user_openid != mobile2openid[str(mobile)]:
                        ReferalBonusRecord.objects.create(user_openid=user_openid,
                                                      referal_user_openid=mobile2openid[str(mobile)],
                                                      trade_id=trade.id,
                                                      bonus_value = int(trade.payment * 5),
                                                      confirmed_status=1)
                    
        rs = ReferalBonusRecord.objects.filter(user_openid=user_openid)
        for r in rs:
            referal_bonus += r.bonus_value * 0.01
        
        response = render_to_response('weixin/ambass.html', 
                                  {'openid':user_openid, 
                                   'referal_count':referal_count, 
                                   'referal_bonus':referal_bonus,
                                   'vipcode':vipcode, 'coupon':coupon,
                                   'payment':payment, 'num_orders':len(effect_mobiles),
                                   'effect_mobiles':effect_mobiles,
                                   'coupon_click_count':coupon_click_count}, 
                                  context_instance=RequestContext(request))
        response.set_cookie("openid",user_openid)
        return response


class RefundSubmitView(View):
    def post(self, request):
        content = request.REQUEST
        tradeid = content.get("tradeid")
        refundtype = content.get("refund_type")
        vipcode = content.get("vipcode")
        bank_account = content.get("bank_account")
        account_owner = content.get("account_owner")

        user_openid = request.COOKIES.get('openid')
        mergetrades = MergeTrade.objects.filter(id=int(tradeid))
        mobile = mergetrades[0].receiver_mobile

        review_note = '|'.join([bank_account, account_owner])
        
        obj = Refund.objects.filter(trade_id=tradeid)
        if obj.count() < 1:
            if refundtype == "0":
                obj = Refund.objects.create(trade_id=int(tradeid),refund_type=int(refundtype),user_openid=user_openid,mobile=mobile)
            else:
                obj = Refund.objects.create(trade_id=int(tradeid),refund_type=int(refundtype),vip_code=vipcode,review_note=review_note,user_openid=user_openid,mobile=mobile)
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
        for refund in refundlist:
            refund.pay_amount = refund.pay_amount * 0.01
        
        response = render_to_response('weixin/refundreview.html', 
                                      {"refundlist":refundlist, "refund_status":refund_status},
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

            refunds = Refund.objects.filter(pk=refund_id)
            refunds.update(pay_type=pay_type,pay_amount=pay_amount,review_note=review_note,refund_status=action)
            
            mergetrades = MergeTrade.objects.filter(id=refunds[0].trade_id)
        
        refunds = Refund.objects.filter(pk__gt=refund_id).filter(refund_status=refund_status).order_by('pk')[0:1]
        next_trade,next_refund,sample_order = None,None,None
        if refunds.count() > 0:
            next_refund = refunds[0]
            next_refund.pay_amount = next_refund.pay_amount * 0.01
            mergetrades = MergeTrade.objects.filter(id=next_refund.trade_id)
            if mergetrades.count() > 0:
                next_trade = mergetrades[0]
                mobile = next_trade.receiver_mobile
                wx_users = WeiXinUser.objects.filter(mobile=mobile)
                if wx_users.count() > 0:
                    openid = wx_users[0].openid
                    orders = SampleOrder.objects.filter(user_openid=openid).filter(status__gt=0).filter(status__lt=7)
                    if orders.count() > 0:
                        sample_order = orders[0]

        html = 'weixin/refundreviewblock.html'
        if refund_status == 1:
            html = 'weixin/finalizeblock.html'
        response = render_to_response(html, {"first_refund":next_refund, "first_trade": next_trade},
                                      context_instance=RequestContext(request))
        return response
    

class RefundRecordView(View):
    def get(self, request):
        content = request.REQUEST
        refund_id = int(content.get("refund_id"))
        refund_status = int(content.get("refund_status"))
        
        refund = Refund.objects.get(pk=refund_id)
        trade,sample_order = None,None
        
        refund.pay_amount = refund.pay_amount * 0.01
        mergetrades = MergeTrade.objects.filter(id=refund.trade_id)
        if mergetrades.count() > 0:
            trade = mergetrades[0]
            mobile = trade.receiver_mobile
            wx_users = WeiXinUser.objects.filter(mobile=mobile)
            if wx_users.count() > 0:
                openid = wx_users[0].openid
                orders = SampleOrder.objects.filter(user_openid=openid).filter(status__gt=0)
                if orders.count() > 0:
                    sample_order = orders[0]

        html = 'weixin/refundreviewblock.html'
        if refund_status == 1:
            html = 'weixin/finalizeblock.html'    
        response = render_to_response(html, {"first_refund":refund, "first_trade": trade,
                                             "sample_order":sample_order},
                                      context_instance=RequestContext(request))
        return response
        

        
class FreeSampleView(View):
    def get(self, request):
        content = request.REQUEST
        code = content.get('code')
        user_openid = get_user_openid(request, code)

        user_isvalid = False
        wx_user = None
        wx_users = WeiXinUser.objects.filter(openid=user_openid)
        if wx_users.count() > 0:
            wx_user = wx_users[0]
            user_isvalid = wx_user.isValid()

        start = datetime.datetime(2014,8,30)
        now = datetime.datetime.now()
        diff = start - now
        days_left = diff.days
        hours_left = diff.seconds / 3600

        slots_left = 800
        started = False
        if now > start:
            started = True
        
        samples = FreeSample.objects.filter(expiry__gt=datetime.datetime.now())

        order_exists = False
        tmp_time = datetime.datetime(2014,8,27)
        orders = SampleOrder.objects.filter(user_openid=user_openid).filter(created__gt=tmp_time)
        if orders.count() > 0 and not wx_user.isNone():
            order_exists = True
        
        vip_exists = False
        vipcode = None
        if wx_user and wx_user.vipcodes.count() > 0:
            vipcode_obj = wx_user.vipcodes.all()[0]
            if vipcode_obj.created < datetime.datetime(2014,8,15):
                vip_exists = True
                vipcode = vipcode_obj.code
        
        today = datetime.date.today()
        start_time = datetime.datetime(today.year, today.month, today.day)
        today_orders = SampleOrder.objects.filter(created__gt=start_time).count()
        
        pk = None
        if wx_user:
            pk = wx_user.pk
            
        response = render_to_response('weixin/freesamples.html', 
                                      {"samples":samples, 
                                       "today_orders":today_orders,
                                       "user_isvalid":user_isvalid, 
                                       "order_exists":order_exists, 
                                       "days_left":days_left,
                                       "hours_left":hours_left,
                                       "slots_left":slots_left,
                                       "started":started,"openid":user_openid,
                                       "vip_exists":vip_exists,
                                       "vipcode":vipcode,
                                       "pk":pk},
                                      context_instance=RequestContext(request))
        response.set_cookie("openid",user_openid)
        return response


from django.shortcuts import redirect

class VipCodeVerifyView(View):
    def get(self, request):
        content = request.REQUEST
        vipcode = content.get("vipcode")
        
        response = {"code":"bad"}
        vipcodes = VipCode.objects.filter(code=vipcode)
        if vipcodes.count() > 0:
            response = {"code":"good"}
        
        return HttpResponse(json.dumps(response),mimetype='application/json')

        

class SampleApplyView(View):
    def get(self, request):
        return redirect("/weixin/sampleads/0/")

    def post(self, request):

        content = request.REQUEST
        sample_pk = content.get("sample_pk")
        color = content.get("color")
        size = content.get("size")
        weight = content.get("weight")
        vipcode = content.get("vipcode")
        vip_exists = content.get("vip_exists")
        
        if vip_exists != "1":
            vipcodes = VipCode.objects.filter(code=vipcode)
            if vipcodes.count() <= 0:
                return redirect("/weixin/sampleads/0/")
            
        sku_code = ''.join([color, size, weight])
        
        sample = FreeSample.objects.get(pk=int(sample_pk))

        skus = SampleSku.objects.filter(sku_code=sku_code)
        sku = skus[0]

        code = content.get('code')
        user_openid = get_user_openid(request, code)
        wx_user = None
        users = WeiXinUser.objects.filter(openid=user_openid)
        if users.count() > 0:
            wx_user = users[0]

        if wx_user.isValid() == False:
	  redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://weixin.huyi.so/weixin/babyinfo/&response_type=code&scope=snsapi_base&state=135#wechat_redirect"
          return redirect(redirect_url)

        response = render_to_response('weixin/sampleapply.html',
                                      {"sample":sample, "sku":sku, "wx_user": wx_user, 
                                       "vipcode":vipcode, "vip_exists":vip_exists},
                                      context_instance=RequestContext(request))
        response.set_cookie("openid",user_openid)
        return response
    
class SampleConfirmView(View):
    def post(self, request):
        content = request.REQUEST
        sample_pk = int(content.get("sample_pk","0"))
        sku_code = content.get("sku_code","0")
        p1 = content.get("p1","0")
        p2 = content.get("p2","0")
        p3 = content.get("p3","0")
        vipcode = content.get("vipcode","0")
        vip_exists = content.get("vip_exists", "0")
        score = int(p1) + int(p2) + int(p3)
        
        user_openid = request.COOKIES.get('openid')

        user = WeiXinUser.objects.filter(openid=user_openid)        
        redirect_url = '/weixin/sampleads/%d/' % user[0].pk

        start_time = datetime.datetime(2014,8,12)
        order = SampleOrder.objects.filter(user_openid=user_openid).filter(created__gt=start_time)
        if order.count() > 0:
            return redirect(redirect_url)

        sample = FreeSample.objects.get(pk=sample_pk)
        sample.sample_orders.create(sku_code=sku_code,user_openid=user_openid,vipcode=vipcode,problem_score=score)
        
        if vip_exists == "0":
            VipCode.objects.filter(code=vipcode).update(usage_count=F('usage_count')+1)

        #VipCode.objects.genVipCodeByWXUser(user)
        
        return redirect(redirect_url)

        
class SampleAdsView(View):
    def get(self, request, *args, **kwargs):
        wx_user_pk = kwargs.get('pk',0)
        users = WeiXinUser.objects.filter(pk=wx_user_pk)
        
        openid = request.COOKIES.get('openid')
        
        identical = False
        if users.count() > 0:
            if users[0].vipcodes.count() > 0:
                vipcode = users[0].vipcodes.all()[0].code
            else:
                vipcode = VipCode.objects.genVipCodeByWXUser(users[0])

            if users[0].openid == openid:
                identical = True

            response = render_to_response('weixin/sampleads.html', 
                                          {"identical":identical,"vipcode":vipcode}, 
                                          context_instance=RequestContext(request))
            return response

        vipcode = '898786' ## 'other' case
        response = render_to_response('weixin/sampleads.html',         
                                      {"identical":identical,"vipcode":vipcode}, 
                                      context_instance=RequestContext(request))
        return response
        

class ResultView(View):
    def get(self, request):
        content = request.REQUEST
        code = content.get('code')
        user_openid = get_user_openid(request, code)

        end = datetime.datetime(2014,8,11)
        now = datetime.datetime.now()
        diff = end - now
        days_left = diff.days
        hours_left = diff.seconds / 3600


        order = SampleOrder.objects.filter(user_openid=user_openid)
        has_order = False
        order_status = 0
        if order.count() > 0:
            has_order = True
            order_status = order[0].status
            
        five_batch = SampleOrder.objects.filter(status__gt=0).filter(status__lt=6).count()
        six_batch = SampleOrder.objects.filter(status=6).count()
        slots_left = 1000 - five_batch
        
        usage_count = 0
        users = WeiXinUser.objects.filter(openid=user_openid)
        pk = 1
        vipcode = 0
        if users.count() > 0:
            pk = users[0].pk
            if users[0].vipcodes.count() > 0:
                code_obj = users[0].vipcodes.all()[0]
                usage_count = code_obj.usage_count
                vipcode = code_obj.code

        response = render_to_response('weixin/invite_result.html',
                                      {'days_left':days_left, 'hours_left':hours_left,
                                       'slots_left':slots_left, 'has_order':has_order,
                                       'order_status':order_status, 'vipcode':vipcode, 
                                       'usage_count':usage_count, 'five_batch':five_batch, 
                                       'six_batch':six_batch, 'pk':pk},
                                      context_instance=RequestContext(request))
        response.set_cookie("openid",user_openid)        
        return response


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
class FinalListView(View):
    def get(self, request, *args, **kwargs):

        page = int(kwargs.get('page',1))
        batch = int(kwargs.get('batch',1))
        month = int(kwargs.get('month',8))
        
        start_time = datetime.datetime(2014,8,30)
        end_time = datetime.datetime(2014,9,7)
        order_list = None
        
        if month == 8:
            start_time = datetime.datetime(2014,8,1)
            end_time = datetime.datetime(2014,8,12)

        order_list = SampleOrder.objects.filter(status__gt=0).filter(status__lt=7).filter(created__lt=end_time).filter(created__gt=start_time)
        
        num_per_page = 20 # Show 20 contacts per page
        paginator = Paginator(order_list, num_per_page) 

        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items = paginator.page(paginator.num_pages)

        
        openids = [item.user_openid for item in items]
        wx_users = WeiXinUser.objects.filter(openid__in=openids)
        items = []
        for user in wx_users:
            mobile = ''.join([user.mobile[0:3], "****", user.mobile[7:11]])
            items.append([mobile, user.vipcodes.all()[0].usage_count])

        total = order_list.count()
        num_pages = paginator.num_pages
        next_page = min(page + 1, num_pages)
        prev_page = max(page - 1, 1)
        response = render_to_response('weixin/final_list.html', 
                                      {"items":items, 'num_pages':num_pages, 
                                       'total':total, 'num_per_page':num_per_page,
                                       'prev_page':prev_page, 'next_page':next_page,
                                       'page':page, 'batch':batch, 'month':month},
                                      context_instance=RequestContext(request))
        return response


class PayGuideView(View):
    def get(self, request):
        user_openid = request.COOKIES.get('openid')
        
        user_valid = True
        if user_openid == 'None' or user_openid == None:
            user_valid = False
            
        passed = False
        if user_valid == True:
            orders = SampleOrder.objects.filter(user_openid=user_openid).filter(status__gt=0)
            if orders.count() > 0:
                passed = True
            
        response = render_to_response('weixin/pai_guide.html', {"passed":passed},
                                      context_instance=RequestContext(request))
        return response


class CouponView(View):
    def get(self, request, *args, **kwargs):
        wx_user_pk = int(kwargs.get("user_pk"))
        coupon_pk = int(kwargs.get("coupon_pk"))

        content = request.REQUEST
        vipcode = content.get("vipcode","0")
        
        coupon = Coupon.objects.get(pk=coupon_pk)
        wx_user = WeiXinUser.objects.get(pk=wx_user_pk)

        if wx_user.couponclicks.count() < 1:
            CouponClick.objects.create(coupon=coupon,wx_user=wx_user,vipcode=vipcode)
        
        coupon_url = coupon.coupon_url
        
        return redirect(coupon_url)


class VipCouponView(View):
    def get(self, request):
        content = request.REQUEST
        code = content.get('code')
        user_openid = get_user_openid(request, code)
        
        weixin_user_service = WeixinUserService(user_openid)
        wx_user = weixin_user_service._wx_user
        
        title = u'VIP优惠券'
        if wx_user.isValid() == False:
            response = render_to_response('weixin/remind.html', {"title":title, "openid":user_openid},context_instance=RequestContext(request))
            response.set_cookie("openid",user_openid)
            return response
        
        response = render_to_response('weixin/vipcoupon.html', {"openid":user_openid, "coupon_pk":"1"},
                                      context_instance=RequestContext(request))
        response.set_cookie("openid",user_openid)        
        return response


class CouponFaqView(View):
    def get(self, request):
        response = render_to_response('weixin/coupon_faq.html', 
                                      context_instance=RequestContext(request))
        return response
        

class RequestCouponView(View):
    def get(self, request):
        content = request.REQUEST
        vipcode = content.get("vipcode")
        openid = content.get("openid")
        coupon_pk = int(content.get("coupon_pk","0"))
        
        coupon = Coupon.objects.get(pk=coupon_pk)
        
        users = WeiXinUser.objects.filter(openid=openid)
        wx_user = users[0]

        vipcodes = VipCode.objects.filter(code=vipcode)
        if vipcodes.count() > 0:
            vipcode_obj = vipcodes[0]
            cc = CouponClick.objects.filter(coupon=coupon).filter(wx_user=wx_user).filter(vipcode=vipcode_obj.code)
            if cc.count() < 1:
                CouponClick.objects.create(coupon=coupon,wx_user=wx_user,vipcode=vipcode_obj.code)
            response = {"code":"ok"}
            return HttpResponse(json.dumps(response),mimetype='application/json')

        response = {"code":"bad"}
        return HttpResponse(json.dumps(response),mimetype='application/json')


class SurveyView(View):
    def get(self, request):
        user_openid = request.COOKIES.get('openid')
        
        exist = False
        wx_users = WeiXinUser.objects.filter(openid=user_openid)
        if wx_users.count() > 0:
            wx_user = wx_users[0]
            if wx_user.surveys.all().count() > 0:
                exist = True
            
        total = Survey.objects.all().count()
        choice1 = Survey.objects.filter(selection=1).count()
        ratio1 = choice1 * 100.0/ total
        ratio2 = 100 - ratio1
        ratio1 = "%.2f" % ratio1
        ratio2 = "%.2f" % ratio2
        response = render_to_response('weixin/survey.html', 
                                      {"exist":exist, "total":total, "ratio1":ratio1, "ratio2":ratio2},
                                      context_instance=RequestContext(request))
        response.set_cookie("openid",user_openid)
        return response

    def post(self, request):
        content = request.REQUEST
        selection = int(content.get("selection","0"))
        user_openid = request.COOKIES.get('openid')
        
        wx_users = WeiXinUser.objects.filter(openid=user_openid)
        if wx_users.count() > 0:
            wx_user = wx_users[0]
            if wx_user.surveys.all().count() < 1:
                Survey.objects.create(selection=selection,wx_user=wx_user)
                response = {"code":"ok"}
                return HttpResponse(json.dumps(response),mimetype='application/json')

        response = {"code":"bad"}
        return HttpResponse(json.dumps(response),mimetype='application/json')

    
class TestView(View):
    def get(self, request):
        response = render_to_response('weixin/unilittles_story.html', 
                                      context_instance=RequestContext(request))
        return response
        
