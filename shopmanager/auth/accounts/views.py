#-*- coding:utf8 -*-
from django.http import HttpResponse,HttpResponseRedirect,HttpResponseBadRequest
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, SESSION_KEY
from django.contrib.auth.decorators import login_required
from shopback.signals import taobao_logged_in
from shopback.orders.models import Trade
from auth.utils import parse_urlparams,parse_datetime
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
 
    if not user:
        return HttpResponseRedirect('/admin/')

    if user.is_anonymous():
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
#    return HttpResponse('ok')
    return HttpResponseRedirect('/app/autolist/')


def print_iterables(item):
    if not hasattr(item, 'iteritems'):
        print item
        return
    for k,v in item.iteritems():
        print k, ':',
        print_iterables(v)

def test_api(request):
    #profile = request.user.get_profile()
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
    
#    response = apis.taobao_fenxiao_orders_get(purchase_order_id=54483385,tb_user_id=profile.visitor_id) 
#    print response
    #user_id = profile.visitor_id
    
#    response = apis.taobao_item_update_listing(num_iid='19554132278',num='5104',tb_user_id=user_id)
#    print response
    
#    response_list = apis.taobao_increment_customer_permit(tb_user_id=174265168)
#    print 'response list:',response_list
    
#    response =  apis.taobao_item_skus_get(num_iids='15065195444',tb_user_id=174265168)  
#    print response

#    response = apis.taobao_item_sku_get(num_iid='15065195444',sku_id='1627207',tb_user_id=174265168)
#    print response

    #response = apis.taobao_itempropvalues_get(cid='50012413',pvs='1627207:3232478',type=1,tb_user_id=174265168)
    #res = response["itempropvalues_get_response"]["prop_values"]["prop_value"]

#    url = 'http://stream.api.taobao.com/stream'
#    import time
#    import urllib
#    import pycurl,StringIO
#    #import urllib3 
#    from auth.utils import getSignatureTaoBao
#    USER_AGENT = 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.1) Gecko/2008071620 Firefox/3.0.1'
#    HEADERS = ['Accept-Language: en-us,en;q=0.5', 'Accept-Encoding: gzip,deflate', 'Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7', 'Keep-Alive: 300', 'Connection: Keep-Alive']
#
#    
#    params = {}
#    params['app_key'] = '21165266'
##    params['user']    = '174265168'
#    params['v']       = '2.0'
#    params['format']  = 'json'
#    params['sign_method']    = 'md5'
#    params['timestamp'] = int(time.time())
#    params['sign']    = getSignatureTaoBao(params,'ea5f5687a856ec58199d538cfa04496d')
#    
##    print params
##    manager = urllib3.PoolManager(10,headers=HEADERS)
##    r = manager.request('POST',url,fields=params)
##    http_pool = urllib3.connection_from_url(url)
##    r         = http_pool.post_url('/stream', params)
##    print r.headers
##
##    print r.data
#    
#    def body(buf):
#        import sys
#        sys.stdout.write('body :'+buf)
#        
#    def header(buf):
#        import sys
#        sys.stderr.write('header :'+buf)
#    
#    #dev_null = StringIO.StringIO()
#    pycurlConnect = pycurl.Curl()
#    #pycurlConnect.setopt(pycurl.HTTPHEADER, HEADERS)
#    pycurlConnect.setopt(pycurl.URL, url)
#    pycurlConnect.setopt(pycurl.POSTFIELDS, urllib.urlencode(params))
#    pycurlConnect.setopt(pycurl.WRITEFUNCTION,body)
#    pycurlConnect.setopt(pycurl.HEADERFUNCTION,header)
#    #pycurlConnect.setopt(pycurl.POST, 1)
#    #pycurlConnect.setopt(pycurl.VERBOSE, 1)
#    pycurlConnect.perform()
#    pycurlConnect.close()
#    print dev_null.getvalue()
#    dev_null.close()
#
#    response = apis.taobao_comet_discardinfo_get(start='2012-11-21 15:45:00',end='2012-11-21 16:00:00',tb_user_id=174265168)
#    print response

#    response  = apis.taobao_increment_trades_get(nick=u'优尼世界旗舰店',start_modified='2012-11-13 14:00:00',end_modified='2012-11-13 14:35:00',page_no=1,page_size=10,tb_user_id=174265168)
#    print response
#    response_list = apis.taobao_trades_sold_increment_get(tb_user_id='121741189',page_no=1,fields='tid,modified'
#            ,page_size=settings.TAOBAO_PAGE_SIZE,use_has_next='true',start_modified='2012-10-24 15:00:00',end_modified='2012-10-24 16:25:00')
#    print response_list

#    from shopback.orders.models import Trade,Order
#    response = apis.taobao_trade_fullinfo_get(tid=251739089889670,tb_user_id=174265168)
#    trade = Trade.save_trade_through_dict(174265168,response['trade_fullinfo_get_response']['trade'])
#    print response

#    from shopback.trades.models import WAIT_SELLER_SEND_GOODS
#    response_list = apis.taobao_trades_sold_get(start_created=None,end_created=None,page_no=1,page_size=10,
#                           use_has_next='true',status="WAIT_SELLER_SEND_GOODS",type=None,
#                           fields='tid,modified',tb_user_id='174265168')
#    print len(response_list['trades_sold_get_response']['trades']['trade'])
    #response = apis.taobao_item_skus_get(num_iids="14443413131,4037729908",tb_user_id=174265168)
    #print response

#    response = apis.taobao_increment_customer_permit(tb_user_id=174265168)
#    print response
    
#    response = apis.taobao_increment_authorize_message_get(nick='优尼世界旗舰店',topic='item',tb_user_id=174265168)
#    print response
    
#    response = apis.taobao_fenxiao_orders_get(tb_user_id=174265168,fields='fenxiao_id,id',page_no=1,start_created='2012-11-17 00:00:00',end_created='2012-11-22 00:00:00'
#                                              ,time_type='trade_time_type',page_size=50,status='WAIT_SELLER_SEND_GOODS')
#    print response
    
#    response = apis.taobao_logistics_orders_detail_get(tid=61119154,tb_user_id=174265168)
#    print response

#    response = apis.taobao_itemcats_increment_get(cids='50008165,50014812',type=1,days=1,tb_user_id=174265168)
#    print 'debug response:',response

#    response = apis.taobao_topats_result_get(task_id=60646019,tb_user_id=121741189)
#    print response

    response = apis.taobao_item_get(num_iid=20489004618,tb_user_id=121741189)
    print response

    return HttpResponseBadRequest('error') #HttpResponse('ok')

