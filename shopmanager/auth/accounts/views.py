#-*- coding:utf8 -*-
from django.http import HttpResponse,HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, SESSION_KEY
from django.contrib.auth.decorators import login_required
from shopback.signals import taobao_logged_in
from auth.utils import verifySignature,decodeBase64String,parse_urlparams,getSignatureTaoBao,refresh_session
from auth import apis

import logging
logger = logging.getLogger('taobao.auth')


def request_taobo(request):

    redirect_url = '%s?response_type=code&client_id=%s&redirect_uri=%s&view=web&scope=%s&state=autolist'%\
                   (settings.AUTHRIZE_URL,settings.APPKEY,settings.REDIRECT_URI,settings.SCOPE)

    return HttpResponseRedirect(redirect_url)



@csrf_exempt
def login_taobo(request):
    
    user = authenticate(request=request)

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

    profile = request.user.get_profile()
    
#    response = apis.taobao_logistics_orders_get(tid=160781477791809,tb_user_id=profile.visitor_id)
#    print response
    
#    response = apis.taobao_fenxiao_products_get(tb_user_id=profile.visitor_id)
#    print response
    
#    response = apis.taobao_item_get(num_iid=9265927875,tb_user_id=profile.visitor_id)
#    print 'response:',response


#    response = apis.taobao_fenxiao_orders_get(page_no=1,
#                time_type='trade_time_type',page_size=10,start_created='2012-06-01',end_created='2012-06-30',tb_user_id=profile.visitor_id)
#    print 'response:',response
#

#    response = apis.taobao_trade_fullinfo_get(tid='166803076931050',tb_user_id=profile.visitor_id)
#    print response

#    orders_list = apis.taobao_refunds_receive_get(tb_user_id=profile.visitor_id,page_no=1,page_size=100,
#                 type='fenxiao',start_modified='2012-03-01 00:00:00',end_modified='2012-05-20 23:59:59')
#    print orders_list
#    trades = apis.taobao_trades_sold_get(tb_user_id=profile.visitor_id,page_no=1
#                 ,page_size=5,use_has_next='true',start_created='2012-03-10 00:00:00',end_created='2012-05-15 00:00:00',type='cod')
#    print 'trades:',trades
#    for t in trades['trades_sold_get_response']['trades']['trade']:
#        print t
#        trade_info = apis.taobao_trade_amount_get(tid=t['tid'],session=profile.top_session)
#        print trade_info
    return HttpResponse('ok')
    #return HttpResponseRedirect('/app/autolist/')


def test_api(request):
    profile = request.user.get_profile()
#    response = apis.taobao_trade_fullinfo_get(tid='166803076931050',tb_user_id=profile.visitor_id)
#    print response
#    from shopback.signals import merge_trade_signal
#    from shopback.orders.models import Trade
#    trade = Trade.objects.get(id=207583442858125)
#    merge_trade_signal.send(sender=Trade,trade=trade)
#
#    response = apis.taobao_topats_itemcats_get(seller_type='B',cids=25,output_format='csv',tb_user_id=profile.visitor_id)
#    print response 

#    import datetime
#    
#    dt = datetime.datetime.now()
#    dt_t = dt - datetime.timedelta(1,0,0)
#    dt_ago = dt-datetime.timedelta(30,0,0)
#    
#    end     = dt_t.strftime("%Y%m%d")
#    start   = dt_ago.strftime("%Y%m%d")
#    response = apis.taobao_topats_trades_sold_get(start_time=start,end_time=end,tb_user_id=profile.visitor_id)
#    print response

#    response = apis.taobao_topats_result_get(task_id=37606086,tb_user_id=profile.visitor_id)
#    print response

    response = apis.taobao_item_get(num_iid='15065507658',tb_user_id=profile.visitor_id)
    print response

    return HttpResponse('ok')