from django.http import HttpResponse,HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate, login, SESSION_KEY
from django.contrib.auth.decorators import login_required
from shopback.users.signals import taobao_logged_in
from auth.utils import verifySignature,decodeBase64String,parse_urlparams,getSignatureTaoBao,refresh_session
from auth import apis

import logging
logger = logging.getLogger('taobao.auth')


def request_taobo(request):

    redirect_url = '%s?response_type=code&client_id=%s&redirect_uri=%s&scope=%s&view=web&state=autolist'%\
                   (settings.AUTHRIZE_URL,settings.APPKEY,settings.REDIRECT_URI,settings.SCOPE)

    return HttpResponseRedirect(redirect_url)


def login_taobo(request):

    user = authenticate(request=request)
    print user
    if not user or user.is_anonymous():
        return HttpResponseRedirect(reverse('home_page'))

    request.session[SESSION_KEY] = user.id

    login(request, user)

    top_session = request.session.get('top_session',None)
    top_parameters = request.session.get('top_parameters',None)

    taobao_logged_in.send(sender='web',user=user,top_session=top_session,top_parameters=top_parameters)

    logger.info('user %s logged in.' % user.username)

    if request.GET.get('next'):
        return HttpResponseRedirect(request.GET.get('next'))
    else:
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)


@login_required(login_url=settings.LOGIN_URL)
def home(request):

#    profile = user.get_profile()

#    orders_list = apis.taobao_refunds_receive_get(session=profile.top_session,page_no=1,page_size=100,
#                 type='fenxiao',start_modified='2012-03-01 00:00:00',end_modified='2012-05-20 23:59:59')
#    print orders_list
#    trades = apis.taobao_trades_sold_get(session=profile.top_session,page_no=1
#                 ,page_size=10,use_has_next='true',start_created='2012-05-10 00:00:00',end_created='2012-05-15 00:00:00')
#    for t in trades['trades_sold_get_response']['trades']['trade']:
#        print t
#        trade_info = apis.taobao_trade_amount_get(tid=t['tid'],session=profile.top_session)
#        print trade_info

    return HttpResponseRedirect('/autolist/')


