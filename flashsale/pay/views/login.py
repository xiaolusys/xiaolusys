# -*- encoding:utf8 -*-
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.template import RequestContext
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth import authenticate, login as auth_login, SESSION_KEY

from urlparse import urljoin
from flashsale.pay.decorators import weixin_xlmm_auth, weixin_test_auth
from core.weixin import options
from flashsale.pay.models import Customer

import logging

logger = logging.getLogger('django.request')


def flashsale_login(request):
    next_url = request.GET.get(REDIRECT_FIELD_NAME, reverse('sale_home'))
    if request.method == 'GET':

        defaults = {
            "title": u'登录',
            REDIRECT_FIELD_NAME: next_url
        }
        return render(
            request,
            "pay/mlogin.html", defaults,
        )
    else:
        req_params = request.POST
        user = authenticate(request=request, **req_params)
        if not user or user.is_anonymous():
            defaults = {
                "title": u'登录',
                REDIRECT_FIELD_NAME: next_url
            }
            return render(
                request,
                "pay/mlogin.html", defaults,
            )
        request.session[SESSION_KEY] = user.id
        auth_login(request, user)
        return HttpResponseRedirect(next_url)


def productlist_redirect(request):
    return HttpResponseRedirect(urljoin(settings.M_SITE_URL, reverse('rest_v1:weixin-login')))


@weixin_xlmm_auth(redirecto=urljoin(settings.M_SITE_URL, '/pages/denglu.html'))
def weixin_login(request):
    next_url = request.GET.get('next', '/')
    response = HttpResponseRedirect(next_url)

    customer = Customer.objects.get(user=request.user.id)
    openid, unionid = customer.get_openid_and_unoinid_by_appkey(settings.WXPAY_APPID)

    options.set_cookie_openid(response, settings.WXPAY_APPID, openid, unionid)
    return response


@weixin_test_auth(redirecto=urljoin(settings.M_SITE_URL, '/pages/denglu.html'))
def weixin_test(request):
    next_url = request.GET.get('next')
    if next_url:
        return HttpResponseRedirect(next_url)
    return HttpResponseRedirect('/')


from flashsale.pay.tasks import task_Merge_Sale_Customer


def weixin_auth_and_redirect(request):
    next_url = request.GET.get('next')
    code = request.GET.get('code')
    user_agent = request.META.get('HTTP_USER_AGENT')
    if not user_agent or user_agent.find('MicroMessenger') < 0:
        return HttpResponseRedirect(next_url)

    user = request.user
    if not user or user.is_anonymous():
        return HttpResponseRedirect(next_url)

    if not code:
        params = {'appid': settings.WXPAY_APPID,
                  'redirect_uri': request.build_absolute_uri().split('#')[0],
                  'response_type': 'code',
                  'scope': 'snsapi_base',
                  'state': '135'}
        redirect_url = options.gen_weixin_redirect_url(params)
        return HttpResponseRedirect(redirect_url)
    else:
        task_Merge_Sale_Customer.delay(user, code)
        return HttpResponseRedirect(next_url)
