# Create your views here.

import json
from django.http import HttpResponse
from django.shortcuts import redirect,render_to_response
from django.views.generic import View
from django.template import RequestContext

from shopapp.weixin.views import get_user_openid,valid_openid
from models import Clicks, XiaoluMama

import datetime

SHOPURL = "http://mp.weixin.qq.com/bizmall/mallshelf?id=&t=mall/list&biz=MzA5NTI1NjYyNg==&shelf_id=2&showwxpaytitle=1#wechat_redirect"


class StatsView(View):
    def get(self,request):
        
        today = datetime.date.today()
        time_from = datetime.datetime(today.year, today.month, today.day)

        content = request.REQUEST
        pk = content.get('pk')
        if not pk or pk == 'None':
            if request.user:
                pk = request.user.pk
        
        mama_list = XiaoluMama.objects.filter(manager=pk)

        data = []
        for mama in mama_list:
            weikefu = mama.weikefu
            mobile = mama.mobile
            click_list = Clicks.objects.filter(linkid=mama.pk,created__gt=time_from)

            click_num = click_list.count()
            openid_list = click_list.values('openid').distinct()
            
            data_entry = {"mobile":mobile, "weikefu":weikefu, 
                          "click_num":click_num, "user_num":len(openid_list)} 
            data.append(data_entry)

        return render_to_response("stats.html", {"data":data, "pk":int(pk)}, context_instance=RequestContext(request))



def logclicks(request, linkid):
    content = request.REQUEST
    code = content.get('code',None)

    openid = get_user_openid(request, code)

    if not valid_openid(openid):
        redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://weixin.huyi.so/m/%d/&response_type=code&scope=snsapi_base&state=135#wechat_redirect" % int(linkid)
        return redirect(redirect_url)

    Clicks.objects.create(linkid=linkid,openid=openid)
    
    
    return redirect(SHOPURL)
