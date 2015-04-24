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

from models import Clicks, XiaoluMama, AgencyLevel

import logging

logger = logging.getLogger('django.request')


import datetime


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

class MamaStatsView(View):
    def get(self, request):

        content = request.REQUEST
        code = content.get('code',None)

        openid = get_user_openid(request, code)

        if not valid_openid(openid):
            redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://weixin.huyi.so/m/&response_type=code&scope=snsapi_base&state=135#wechat_redirect"
            return redirect(redirect_url)


        
        service = WeixinUserService(openid)
        wx_user = service._wx_user

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
        
        mobile = wx_user.mobile
        
        data = {}
        try:
            xlmm = XiaoluMama.objects.get(mobile=mobile)
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
                    time = str(order.order_create_time)[11:16]
                    order_info = {"nick":"*"+order.buyer_nick[1:], "price":order.order_total_price*0.01,
                                  "time":time, "status":status}
                    order_list.append(order_info)

            order_list.sort(key=lambda a: a["time"])
            click_num = len(openid_list)
            weikefu = xlmm.weikefu
            mobile_revised = "%s****%s" % (mobile[:3], mobile[-4:])

            agencylevel = AgencyLevel.objects.get(pk=xlmm.agencylevel)
            carry = agencylevel.basic_rate * total_value * 0.01

            data = {"mobile":mobile_revised, "click_num":click_num, "weikefu":weikefu,
                    "order_num":order_num, "order_list":order_list, "pk":xlmm.pk,
                    "total_value":total_value, "carry":carry, "agencylevel":agencylevel,
                    "target_date":target_date, "prev_day":prev_day, "next_day":next_day}
        except:
            pass 
        
        response = render_to_response("mama_stats.html", data, context_instance=RequestContext(request))
        response.set_cookie("openid",openid)
        return response



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
            weikefu   = mama.weikefu
            mobile    = mama.mobile
            agencylevel = mama.agencylevel
            click_list = Clicks.objects.filter(linkid=mama.pk,created__gt=time_from,created__lt=time_to)

            click_num = click_list.count()
            openid_list = click_list.values('openid').distinct()
            
            username  = self.getUserName(mama.manager)
            for item in openid_list:
                orders = WXOrder.objects.filter(buyer_openid=item["openid"],
                                                order_create_time__gt=time_from,
                                                order_create_time__lt=time_to)
                if orders.count() > 0:
                    order_num += 1
            
            data_entry = {"mobile":mobile[-4:], "weikefu":weikefu, 
                          "agencylevel":agencylevel,'username':username,
                          "click_num":click_num, "user_num":len(openid_list),
                          "order_num":order_num}
            data.append(data_entry)
            
        return render_to_response("stats.html", 
                                  {'pk':int(pk),"data":data,"managers":managers,"prev_day":prev_day,
                                   "target_date":target_date, "next_day":next_day}, 
                                  context_instance=RequestContext(request))



def logclicks(request, linkid):
    content = request.REQUEST
    code = content.get('code',None)

    openid = get_user_openid(request, code)

    if not valid_openid(openid):
        redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://weixin.huyi.so/m/%d/&response_type=code&scope=snsapi_base&state=135#wechat_redirect" % int(linkid)
        return redirect(redirect_url)

    Clicks.objects.create(linkid=linkid,openid=openid)
    
    
    return redirect(SHOPURL)
