import time
import urllib
from django.http import HttpResponse,HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.signals import user_logged_in
from auth.utils import verifySignature,decodeBase64String,parse_urlparams,getSignatureTaoBao
from auth import apis

import logging
logger = logging.getLogger('taobao.auth')

def request_taobo(request):

    redirect_url = '%s?appkey=%s&encode=utf-8'%(settings.REDIRECT_URL,settings.APPKEY)

    return HttpResponseRedirect(redirect_url)


def login_taobo(request):
    print request.GET
    user = authenticate(request=request)
    print request.session.__dict__
    top_parameters = request.session['top_parameters']
    expires_time = top_parameters['expires_in']
    timestamp = top_parameters['ts']
    if int(expires_time)+int(timestamp) > time.time():
        params = {
            'appkey':settings.APPKEY,
            'refresh_token':top_parameters['refresh_token'],
            'sessionkey':request.session['top_session']
        }
        sign_result = getSignatureTaoBao(params,settings.APPSECRET,both_side=False)
        params['sign'] = sign_result
        refresh_url = '%s?%s'%(settings.REFRESH_URL,urllib.urlencode(params))
        print refresh_url
        return HttpResponseRedirect(refresh_url)


    login(request, user)
    user_logged_in.send(sender='web', user=user, request=request)

    logger.info('user %s logged in.' % user.username)

    #user = apis.taobao_users_get(nicks='coolcuky,horny')

    return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)