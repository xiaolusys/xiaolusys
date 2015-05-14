#-*- coding:utf-8 -*-
# Create your views here.

import json
from django.http import HttpResponse
from django.shortcuts import redirect,render_to_response
from django.views.generic import View
from django.template import RequestContext
from django.contrib.auth.models import User

from shopapp.weixin.views import get_user_openid,valid_openid
from shopapp.weixin.models import WXOrder
from shopapp.weixin.service import WeixinUserService
from shopback.base import log_action, ADDITION, CHANGE

from models import Clicks, XiaoluMama, AgencyLevel, CashOut, CarryLog

from serializers import CashOutSerializer,CarryLogSerializer
from rest_framework import generics
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

import logging
logger = logging.getLogger('django.request')


import datetime, re


WX_WAIT_PAY  = 1
WX_WAIT_SEND = 2
WX_WAIT_CONFIRM = 3
WX_FINISHED  = 5
WX_CLOSE     = 6
WX_FEEDBACK  = 8
    
WXORDER_STATUS = {
    WX_WAIT_PAY:u'待付款',
    WX_WAIT_SEND:u'待发货',
    WX_WAIT_CONFIRM:u'待确认收货',
    WX_FINISHED:u'已完成',
    WX_CLOSE:u'已关闭',
    WX_FEEDBACK:u'维权中'}

SHOPURL = "http://mp.weixin.qq.com/bizmall/mallshelf?id=&t=mall/list&biz=MzA5NTI1NjYyNg==&shelf_id=2&showwxpaytitle=1#wechat_redirect"

def landing(request):
    return render_to_response("mama_landing.html", context_instance=RequestContext(request))

class CashoutView(View):
    def get(self, request):
        content = request.REQUEST
        code = content.get('code',None)

        openid,unionid = get_user_unionid(code,appid=settings.WEIXIN_APPID,
                                          secret=settings.WEIXIN_SECRET)

        if not valid_openid(openid):
            redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://weixin.huyi.so/m/cashout/&response_type=code&scope=snsapi_base&state=135#wechat_redirect"
            return redirect(redirect_url)
        
        xlmm = XiaoluMama.objects.get(openid=unionid)
        referal_list = XiaoluMama.objects.filter(referal_from=xlmm.mobile)
        cashout_objs = CashOut.objects.filter(xlmm=xlmm.pk,status=CashOut.PENDING)
        data = {"xlmm":xlmm, "cashout": cashout_objs.count(), "referal_list":referal_list}
        
        
        response = render_to_response("mama_cashout.html", data, context_instance=RequestContext(request))
        response.set_cookie("openid",openid)
        return response

    def post(self, request):
        content = request.REQUEST
        code = content.get('code',None)
        openid = get_user_openid(request, code)
        v = content.get("v")
        m = re.match(r'^\d+$', v)

        status = {"code":0, "status":"ok"}
        if m:
            value = int(m.group())
            try:
                xlmm = XiaoluMama.objects.get(openid=openid)
                CashOut.objects.create(xlmm=xlmm.pk,value=value)
            except:
                status = {"code":1, "status":"error"}
        else:
            status = {"code":2, "status": "input error"}
            
        return HttpResponse(json.dumps(status),content_type='application/json')



class CashOutList(generics.ListAPIView):
    queryset = CashOut.objects.all().order_by('-created')
    serializer_class = CashOutSerializer
    renderer_classes = (JSONRenderer,)
    filter_fields = ("xlmm",)
    

class CarryLogList(generics.ListAPIView):
    queryset = CarryLog.objects.all().order_by('-created')
    serializer_class = CarryLogSerializer
    renderer_classes = (JSONRenderer,)
    filter_fields = ("xlmm",)
    

from django.conf import settings
from flashsale.pay.options import get_user_unionid
class MamaStatsView(View):
    def get(self, request):
        
        content = request.REQUEST
        code = content.get('code',None)
        
        openid,unionid = get_user_unionid(code,
                                          appid=settings.WEIXIN_APPID,
                                          secret=settings.WEIXIN_SECRET,
                                          request=request)
        
        if not valid_openid(openid):
            redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://weixin.huyi.so/m/m/&response_type=code&scope=snsapi_base&state=135#wechat_redirect"
            return redirect(redirect_url)
        
        service = WeixinUserService(openid,unionId=unionid)
        wx_user = service._wx_user
        
        if not wx_user.isValid():
            return render_to_response("remind.html",{"openid":openid}, 
                                      context_instance=RequestContext(request))
        
        daystr = content.get("day", None)
        today  = datetime.date.today()
        year,month,day = today.year,today.month,today.day
        
        target_date = today
        if daystr:
            year,month,day = daystr.split('-')
            target_date = datetime.date(int(year),int(month),int(day))
            if target_date > today:
                target_date = today
        
        time_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
        time_to = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)
        
        prev_day = target_date - datetime.timedelta(days=1)
        next_day = None
        if target_date < today:
            next_day = target_date + datetime.timedelta(days=1)
        
        mobile = wx_user.mobile
        data   = {}
        try:
            referal_num = XiaoluMama.objects.filter(referal_from=mobile).count()
            xlmm,status = XiaoluMama.objects.get_or_create(openid=unionid)
            if xlmm.mobile  != mobile:
                xlmm.mobile  = mobile
                xlmm.weikefu = wx_user.nickname
                xlmm.save()
            
            clicks = Clicks.objects.filter(linkid=xlmm.pk,created__gt=time_from,created__lt=time_to)
            openid_list = clicks.values("openid").distinct()

            order_num = 0
            total_value = 0
            order_list = []
            for item in openid_list:
                orders = WXOrder.objects.filter(buyer_openid=item["openid"],
                                                order_create_time__gt=time_from,
                                                order_create_time__lt=time_to)
                
                if orders.count() > 0:
                    order_num += 1
                for order in orders:
                    total_value += order.order_total_price*0.01
                    status = WXORDER_STATUS[int(order.order_status)]
                    time   = str(order.order_create_time)[11:16]
                    order_info = {"nick":"*"+order.buyer_nick[1:], 
                                  "price":order.order_total_price*0.01,
                                  "time":time, "status":status}
                    order_list.append(order_info)

            order_list.sort(key=lambda a: a["time"])
            click_num = len(clicks.filter(isvalid=True).values("openid").distinct())
            mobile_revised = "%s****%s" % (mobile[:3], mobile[-4:])

            agencylevel = AgencyLevel.objects.get(pk=xlmm.agencylevel)
            carry = agencylevel.basic_rate * total_value * 0.01

            click_price = 0.2
            if order_num > 2:
                click_price = 0.5
            else:
                click_price += order_num * 0.1

            click_pay = click_price * click_num

            data = {"mobile":mobile_revised, "click_num":click_num, "xlmm":xlmm,
                    "order_num":order_num, "order_list":order_list, "pk":xlmm.pk,
                    "total_value":total_value, "carry":carry, "agencylevel":agencylevel,
                    "target_date":target_date, "prev_day":prev_day, "next_day":next_day,
                    "click_price":click_price, "click_pay":click_pay, "referal_num":referal_num}
        except Exception,exc:
            logger.error(exc.message,exc_info=True)
        
        response = render_to_response("mama_stats.html", data, context_instance=RequestContext(request))
        response.set_cookie("sunionid",unionid)
        response.set_cookie("sopenid",openid)
        return response

from flashsale.clickrebeta.models import StatisticsShoppingByDay
from flashsale.clickcount.models import ClickCount

class StatsView(View):
    
    def getUserName(self,uid):
        try:
            return User.objects.get(pk=uid).username
        except:
            return 'none'
        
    def get(self,request):
        content = request.REQUEST
        daystr = content.get("day", None)
        today = datetime.date.today()
        year,month,day = today.year,today.month,today.day

        target_date = today
        if daystr:
            year,month,day = daystr.split('-')
            target_date = datetime.date(int(year),int(month),int(day))
            if target_date > today:
                target_date = today

        time_from = datetime.datetime(target_date.year, target_date.month, target_date.day)
        time_to = datetime.datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59)
        
        prev_day = target_date - datetime.timedelta(days=1)
        next_day = None
        if target_date < today:
            next_day = target_date + datetime.timedelta(days=1)

        pk = content.get('pk','6')
        mama_list = XiaoluMama.objects.filter(manager=pk)
        mama_managers = XiaoluMama.objects.values('manager').distinct()
        manager_ids   = [m.get('manager') for m in mama_managers if m]
        managers      = User.objects.filter(id__in=manager_ids)
        data = []

        for mama in mama_list:
            order_num = 0
            click_num = 0
            user_num  = 0
            weikefu   = mama.weikefu
            mobile    = mama.mobile
            agencylevel = mama.agencylevel
            username  = self.getUserName(mama.manager)

            # click_list = Clicks.objects.filter(linkid=mama.pk,created__gt=time_from,created__lt=time_to)
            #
            # click_num = click_list.count()
            # openid_list = click_list.values('openid').distinct()
            #

            # for item in openid_list:
            #     orders = WXOrder.objects.filter(buyer_openid=item["openid"],
            #                                     order_create_time__gt=time_from,
            #                                     order_create_time__lt=time_to)
            #     if orders.count() > 0:
            #         order_num += 1

            day_stats = StatisticsShoppingByDay.objects.filter(linkid=mama.pk,tongjidate=target_date)
            if day_stats.count() > 0:
                order_num = day_stats[0].ordernumcount

            click_counts = ClickCount.objects.filter(linkid=mama.pk, date=target_date)
            if click_counts.count() > 0:
                click_num = click_counts[0].click_num
                user_num = click_counts[0].user_num
            else:
                click_list = Clicks.objects.filter(linkid=mama.pk,created__gt=time_from,created__lt=time_to)
                click_num = click_list.count()
                openid_list = click_list.values('openid').distinct()
                user_num = len(openid_list)

            data_entry = {"mobile":mobile[-4:], "weikefu":weikefu,
                          "agencylevel":agencylevel,'username':username,
                          "click_num":click_num, "user_num":user_num,
                          "order_num":order_num}
            data.append(data_entry)
            
        return render_to_response("stats.html", 
                                  {'pk':int(pk),"data":data,"managers":managers,"prev_day":prev_day,
                                   "target_date":target_date, "next_day":next_day}, 
                                  context_instance=RequestContext(request))

from . import tasks

def logclicks(request, linkid):
    content = request.REQUEST
    code = content.get('code',None)

    openid,unionid = get_user_unionid(code,appid=settings.WEIXIN_APPID,
                                          secret=settings.WEIXIN_SECRET)

    if not valid_openid(openid):
        redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://weixin.huyi.so/m/%d/&response_type=code&scope=snsapi_base&state=135#wechat_redirect" % int(linkid)
        return redirect(redirect_url)

    tasks.task_Create_Click_Record.s(linkid, openid)()

    return redirect(SHOPURL)


from django.shortcuts import get_object_or_404
from django.forms import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder

def chargeWXUser(request,pk):
    
    result = {}
    employee = request.user

    xiaolumm = get_object_or_404(XiaoluMama,pk=pk)
   
    charged = XiaoluMama.objects.charge(xiaolumm, employee)
    if not charged:
        result ={'code':1,'error_response':u'已经被接管'}
            
    if charged :
        result ={'success':True}
        
        log_action(request.user.id,xiaolumm,CHANGE,u'接管用户')
    
    return HttpResponse( json.dumps(result),content_type='application/json')


class XiaoluMamaModelView(View):
    """ 微信接收消息接口 """
    
    def post(self,request ,pk):
        
        content    = request.REQUEST
        user_group_id = content.get('user_group_id')
        
        xlmm = get_object_or_404(XiaoluMama,pk=pk)
        xlmm.user_group_id = user_group_id
        xlmm.save()
        
        user_dict = {'code':0,'response_content':
                     model_to_dict(xlmm, fields=['id','user_group','charge_status'])}
        
        return HttpResponse(json.dumps(user_dict,cls=DjangoJSONEncoder),
                            mimetype="application/json")


