from django.http import HttpResponse,HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, SESSION_KEY
from shopback.users.signals import taobao_logged_in
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

    #refresh_session(request.session,settings)
    request.session[SESSION_KEY] = user.id

    login(request, user)

    top_session = request.session.get('top_session',None)
    top_appkey  = request.session.get('top_appkey',None)
    top_parameters = request.session.get('top_parameters',None)

    taobao_logged_in.send(sender='web',user=user,top_session=top_session,top_appkey=top_appkey,top_parameters=top_parameters)


    #content = apis.taobao_item_get(num_iid='4726175562',session=top_session)
    #print 'content:',content

    #print 'session:',dict(request.session)

    #content = apis.taobao_items_get(q='\xe7\x9d\xa1\xe8\xa2\x8b',session=request.session['top_session'],page_no=1,page_size=100)
    #print 'content:',content


    logger.info('user %s logged in.' % user.username)

    if request.GET.get('next'):
        return HttpResponseRedirect(request.GET.get('next'))
    else:
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

def home(request):
    user = authenticate(request=request)
    if not user or user.is_anonymous():
        return HttpResponseRedirect('/accounts/login/')
    return HttpResponseRedirect('/autolist/')
    #return HttpResponse('Welcom to home page!')

