import time
import datetime
from django.http import HttpResponseRedirect
from django.utils.decorators import available_attrs
from functools import wraps

from django.db.models import F
from django.conf import settings
from .models import WeixinLinkClicks, WeixinLinkClickRecord
from shopapp.weixin.views import get_user_openid


def getAuthorizeUrl(req_url):
    return ('{0}?appid={1}&redirect_uri={2}&response_type=code'
            + '&scope=snsapi_base&state=135#wechat_redirect') \
        .format(settings.WEIXIN_AUTHORIZE_URL,
                settings.WEIXIN_APPID,
                req_url)


def record_weixin_clicks(function=None, validated_in=24 * 60 * 60):
    def _decorator(view_func):

        def wrapped_view(request, *args, **kwargs):

            user_agent = request.META.get('HTTP_USER_AGENT')
            if not user_agent or user_agent.find('MicroMessenger') < 0:
                return view_func(request, *args, **kwargs)

            user_openid = request.COOKIES.get("openid")
            code = request.GET.get('code')
            req_url = request.get_full_path().split('?')[0]
            if not user_openid and not code:
                abs_url = request.build_absolute_uri().split('#')[0]
                redirect_url = getAuthorizeUrl(abs_url)
                return HttpResponseRedirect(redirect_url)

            if code and (not user_openid or user_openid.strip() == '' or user_openid == 'None'):
                user_openid = get_user_openid(request, code)

            if not user_openid:
                return view_func(request, *args, **kwargs)

            wlcr_num = WeixinLinkClickRecord.objects.filter(user_openid=user_openid).count()
            if wlcr_num < 4:

                wlcr, state = WeixinLinkClickRecord.objects.get_or_create(user_openid=user_openid, link_url=req_url)
                wlcs = WeixinLinkClicks.objects.filter(link_url=req_url)

                if (state and wlcs.count() > 0 and
                        (not wlcs[0].validated_in or
                                 (datetime.datetime.now() - wlcs[0].created).total_seconds() < validated_in)):
                    clicker_incr = 1
                    WeixinLinkClicks.objects.filter(link_url=req_url) \
                        .update(click_count=F('click_count') + 1,
                                clicker_num=F('clicker_num') + clicker_incr)

            response = view_func(request, *args, **kwargs)

            response.set_cookie("openid", user_openid)

            return response

        return wrapped_view
        # wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)

    if function is None:
        return _decorator
    else:
        return _decorator(function)
