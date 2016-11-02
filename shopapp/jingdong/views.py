# -*- coding:utf8 -*-
import urlparse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, SESSION_KEY
from django.contrib.auth.decorators import login_required
from shopback.signals import user_logged_in
from django.conf import settings

import logging

logger = logging.getLogger('django.request')


def loginJD(request):
    return HttpResponseRedirect('&'.join(
        ['%s?' % settings.JD_AUTHRIZE_URL,
         'response_type=code',
         'client_id=%s' % settings.JD_APP_KEY,
         'redirect_uri=%s' % urlparse.urljoin(settings.SITE_URL,
                                              settings.JD_REDIRECT_URI),
         'state=jingdong']))


def loginAuthJD(request):
    user = authenticate(request=request)

    if not user:
        return HttpResponseRedirect('/admin/')

    if user.is_anonymous():
        return HttpResponseRedirect(reverse('home_page'))

    request.session[SESSION_KEY] = user.id

    login(request, user)

    top_session = request.session.get('top_session', None)
    top_parameters = request.session.get('top_parameters', None)

    user_logged_in.send(sender='jingdong', user=user,
                        top_session=top_session,
                        top_parameters=top_parameters)

    logger.info('user %s logged in.' % user.username)

    if request.GET.get('next'):
        return HttpResponseRedirect(request.GET.get('next'))
    else:
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
