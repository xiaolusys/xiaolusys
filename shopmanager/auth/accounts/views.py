from django.http import HttpResponse,HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login
from django.contrib.auth.signals import user_logged_in
from auth.utils import verifySignature,decodeBase64String,parse_urlparams,getSignatureTaoBao,refresh_session
from auth import apis

import logging
logger = logging.getLogger('taobao.auth')


def request_taobo(request):

    redirect_url = '%s?appkey=%s&encode=utf-8'%(settings.REDIRECT_URL,settings.APPKEY)

    return HttpResponseRedirect(redirect_url)


def login_taobo(request):

    user = authenticate(request=request)

    if not user or user.is_anonymous():
        return HttpResponseRedirect(reverse('home_page'))

    refresh_session(request.session,settings)

    login(request, user)
    user_logged_in.send(sender='web', user=user, request=request)

#    content = apis.taobao_user_get(session=request.session['top_session'])
#    print 'content:',content
#
#    print 'session:',dict(request.session)


    logger.info('user %s logged in.' % user.username)

    if request.GET.get('next'):
        return HttpResponseRedirect(request.GET.get('next'))
    else:
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

def home(request):
    return HttpResponse('Welcom to home page!')

