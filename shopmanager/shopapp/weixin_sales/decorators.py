import time
from django.utils.decorators import  available_attrs
from functools import wraps

from django.db.models import F
from .models import WeixinLinkClicks

def  record_weixin_clicks(function=None,validated_in=24*60*60):
    
    def _decorator(view_func):
        
        def wrapped_view(request,*args,**kwargs):
            
            user_agent = request.META.get('HTTP_USER_AGENT')
            if user_agent.find('MicroMessenger') < 0:
                return view_func(request,*args,**kwargs)
            
            req_url = request.get_full_path()
            link_string = request.COOKIES.get('click_links','')
            link_dict  = dict([(r.split('|')[0],r.split('|')[1]) for r in link_string.split(',') if len(r.split('|')) == 2 ])
            click_time = link_dict.get(req_url,'')
            
            if not click_time or  int(time.time()) - int(click_time) > validated_in :
                WeixinLinkClicks.objects.filter(link_url=req_url).update(
                                                                         click_count=F('click_count') + 1,
                                                                         clicker_num=F('click_count') + click_time and 1 or 0,
                                                                         validated_in=validated_in)
                link_dict[req_url] = int(time.time())
                
            response = view_func(request,*args,**kwargs)
            response.set_cookie("click_links",",".join(["%s|%s"%(r[0],r[1]) for r in link_dict.iteritems()]))
            
            return response

        return wrapped_view
        #wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)
    if function is None:
        return _decorator
    else:
        return _decorator(function)
            