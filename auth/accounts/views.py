# -*- coding:utf8 -*-
import urlparse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, SESSION_KEY
from django.contrib.auth.decorators import login_required
from shopback.signals import user_logged_in
from shopback.orders.models import Trade
from common.utils import parse_urlparams, parse_datetime
from auth import apis

import logging

logger = logging.getLogger('taobao.auth')


def request_taobao(request):
    return HttpResponseRedirect('&'.join(
        ['%s?' % settings.AUTHRIZE_URL,
         'response_type=code',
         'client_id=%s' % settings.APPKEY,
         'redirect_uri=%s' % urlparse.urljoin(settings.SITE_URL,
                                              settings.REDIRECT_URI),
         'view=web',
         'state=taobao']))


@csrf_exempt
def login_taobao(request):
    user = authenticate(request=request)

    if not user:
        return HttpResponseRedirect('/admin/')

    if user.is_anonymous():
        return HttpResponseRedirect(reverse('home_page'))

    request.session[SESSION_KEY] = user.id

    login(request, user)

    top_session = request.session.get('top_session', None)
    top_parameters = request.session.get('top_parameters', None)

    user_logged_in.send(sender='taobao', user=user,
                        top_session=top_session,
                        top_parameters=top_parameters)

    logger.info('user %s logged in.' % user.username)

    if request.GET.get('next'):
        return HttpResponseRedirect(request.GET.get('next'))
    else:
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)


# @login_required(login_url=settings.LOGIN_URL)
def home(request):
    return HttpResponseRedirect('/admin/')


def test_api(request):
    return HttpResponseBadRequest('error')
