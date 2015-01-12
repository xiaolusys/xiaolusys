import time
from django.http import HttpResponseRedirect
from django.utils.decorators import  available_attrs
from functools import wraps

from django.db.models import F
from .models import WeixinLinkClicks,WeixinLinkClickRecord
from shopapp.weixin.views import get_user_openid

def  record_weixin_clicks(function=None,validated_in=24*60*60):
    
    def _decorator(view_func):
        
        def wrapped_view(request,*args,**kwargs):
            
            user_agent = request.META.get('HTTP_USER_AGENT')
            if not user_agent or user_agent.find('MicroMessenger') < 0:
                return view_func(request,*args,**kwargs)
            
            user_openid = request.COOKIES.get("openid")
            code   = request.GET.get('code')
            req_url = request.get_full_path().split('?')[0]
            if not user_openid and not code:
                return HttpResponseRedirect('https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://weixin.huyi.so%s&response_type=code&scope=snsapi_base&state=135#wechat_redirect'%req_url)
            
            if code and not user_openid:
                user_openid = get_user_openid(request,code)
                
            if not user_openid:
                raise Exception("authorize error,code:%s,user_agent:%s"%(code,user_agent))
            
            wlcr_num =  WeixinLinkClickRecord.objects.filter(user_openid=user_openid).count()
            if wlcr_num < 4:
                

            #req_url = request.get_full_path().split('?')[0]
            #link_string = request.COOKIES.get('click_links','')

            #link_dict  = dict([(r.split('|')[0],r.split('|')[1]) for r in link_string.split(',') if len(r.split('|')) == 2 ])
            #click_time = link_dict.get(req_url,'')
            
                wlcr,state = WeixinLinkClickRecord.objects.get_or_create(user_openid=user_openid,link_url=req_url)
            
                if state:#and not click_time or  int(time.time()) - int(click_time) > validated_in :
                
                    clicker_incr = 1 #([1,0][click_time and  1 or (len(link_dict.keys()) > 4 and 1 or 0)])
                    WeixinLinkClicks.objects.filter(link_url=req_url).update(
                                                                         click_count=F('click_count') + 1,
                                                                         clicker_num=F('clicker_num') + clicker_incr,
                                                                         validated_in=validated_in)
                #link_dict[req_url] = int(time.time())
                
            response = view_func(request,*args,**kwargs)
            #response.set_cookie("click_links",",".join(["%s|%s"%(r[0],r[1]) for r in link_dict.iteritems()]))

            response.set_cookie("openid",user_openid)
            
            return response

        return wrapped_view
        #wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)
    if function is None:
        return _decorator
    else:
        return _decorator(function)
            
