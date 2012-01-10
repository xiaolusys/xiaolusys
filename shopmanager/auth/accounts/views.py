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

    refresh_session(request,settings)

    login(request, user)
    user_logged_in.send(sender='web', user=user, request=request)

    logger.info('user %s logged in.' % user.username)

    #products = apis.taobao_products_get(nick=request.session['top_parameters']['visitor_nick'],page_size=100)

    #products = apis.taobao_items_onsale_get(session=request.session['top_session'])

    #print 'debug products:',products   130126150

    #content = apis.taobao_products_search(q='\xe4\xbc\x98\xe5\xb0\xbc\xe4\xb8\x96\xe7\x95\x8c'.decode('utf8'),session=request.session['top_session'])
    #print content

    #content = apis.taobao_items_search(product_id=130126150,session=request.session['top_session'])
    #print 'content:',content

    #content = apis.taobao_items_inventory_get(session=request.session['top_session'])
    #print content

    #content = apis.taobao_items_onsale_get(page_no=0,page_size=100,session=request.session['top_session'])
    #print content

    #ret = apis.taobao_item_update_listing(num_iid=12789208440,num=163,session=request.session['top_session'])
    #print 'debug:',ret

    #content = apis.taobao_item_update_delisting(num_iid=12789208440,session=request.session['top_session'])
    #print content

    content = apis.taobao_item_get(num_iid=12789208440,session=request.session['top_session'])
    print content

    if request.GET.get('next'):
        return HttpResponseRedirect(request.GET.get('next'))
    else:
        return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

def home(request):
    return HttpResponse('Welcom to home page!')

