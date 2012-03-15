import time
import datetime
import json
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db.models import Avg, Variance,Sum
from django.template import RequestContext
from chartit import DataPool, Chart
from chartit import PivotDataPool, PivotChart
from search.crawurldata import getTaoBaoPageRank, getCustomShopsPageRank
from search.models import ProductPageRank,ProductTrade
from auth.utils import parse_datetime, format_time
from autolist.models import ProductItem
from shopback.base.aggregates import ConcatenateDistinct

def getShopsRank(request):
    nicks = request.GET.get('nicks', None)
    keywords = request.GET.get('keywords', None)
    page_nums = int(request.GET.get('page_nums', '5'))

    if not nicks and not keywords:
        return HttpResponse('nicks and keywords can\'t be empty!')

    nicks = nicks.split(',')
    keywords = keywords.split(',')

    results = getCustomShopsPageRank(nicks, keywords, page_nums)

    strings = ''
    for keyword, nicks_result in  results.iteritems():
        for nick, values in nicks_result.iteritems():
            strings += keyword.encode('utf8') + '---------' + nick.encode('utf8') + '<br>'

            for value in values:
                strings += value['item_id'] + '====' + value['title'].encode('utf8') + '=======' + str(
                        value['rank']) + '<br>'

    return HttpResponse(strings)


def getProductPeriodChart(nick, keyword, dt_f, dt_t, index):
    rankqueryset = ProductPageRank.objects.filter(nick=nick, keyword=keyword, created__gt=dt_f, created__lt=dt_t)\
    .values('item_id', 'title').distinct('item_id')

    if rankqueryset.count() == 0:
        return None

    series = []
    series_option = {'options': {'type': 'spline', 'stacking': False}, 'terms': {}}
    for prod in rankqueryset:
        serie = {'options': {
            'source': ProductPageRank.objects.filter
                    (keyword=keyword, created__gt=dt_f, created__lt=dt_t, item_id=prod['item_id'])},
                 'terms': [{'created' + prod['item_id']: 'created'}, {prod['item_id']: 'rank'}]}
        series.append(serie)
        series_option['terms'].update({'created' + prod['item_id']: [prod['item_id']]})

    productpagerankdata = DataPool(series=series)

    productpagerankcht = Chart(
            datasource=productpagerankdata,
            series_options=[series_option],
            chart_options=
                {'chart': {'renderTo': "container" + str(index)},
                 'title': {
                     'text': '%s-%s' % (nick.encode('utf8'), keyword.encode('utf8'))},
                 'xAxis': {'title': {'text': 'per half hour'}, 'type': 'string',
                           'labels':{'rotation': -45,'align':'right',
                                   'style': {'font': 'normal 12px Verdana, sans-serif'}}},
                 'yAxis': {
                     'title': {'text': 'ranks'},
                     'min': 0,
                     'minorGridLineWidth': 0,
                     'gridLineWidth': 0,
                     'alternateGridColor': None,
                     },
                 'plotOptions': {
                     'spline': {
                         'lineWidth': 1, 'states': {'hover': {'lineWidth': 2}},
                         'marker': {
                             'enabled': False,
                             'states': {'hover': {'enabled': True,'symbol': 'cycle','radius': 0,'lineWidth': 1}}
                         },
                     },
                 }
            })

    return productpagerankcht


def genPeriodChart(request, dt_f, dt_t):
    nicks = request.GET.get('nicks')
    keywords = request.GET.get('keywords', None)

    nicks_list = nicks.split(',')
    if not keywords:
        keys = request.user.get_profile().craw_keywords
        keywords_list = keys.split(',') if keys else []
    else:
        keywords_list = keywords.split(',')

    pagerankchts = []

    for keyword in keywords_list:
        for nick in nicks_list:
            index = len(pagerankchts) + 1
            cht = getProductPeriodChart(nick, keyword, dt_f, dt_t, index)
            if cht:
                pagerankchts.append(cht)

    if not pagerankchts:
        return HttpResponse('nick is not avalible under this keyword.')

    rankqueryset = ProductPageRank.objects.filter\
            (nick__in=nicks_list, keyword__in=keywords_list, created__gt=dt_f, created__lt=dt_t)\
    .values('item_id', 'nick', 'title').distinct('item_id')

    for item in  rankqueryset:
        try:
            product = ProductItem.objects.get(num_iid=item['item_id'])
            item['pic_url'] = product.pic_url
        except:
            pass

    params = {'keywordsrankcharts': pagerankchts, 'items': rankqueryset}

    return render_to_response('keywords_itemsrank.html', params, context_instance=RequestContext(request))


def getItemKeywordsChart(item_id, dt_f, dt_t, index):
    queryset = ProductPageRank.objects.filter(item_id=item_id, created__gt=dt_f, created__lt=dt_t)\
        .values('keyword').distinct('keyword')

    if queryset.count() == 0:
        return None

    series = []
    series_option = {'options': {'type': 'spline', 'stacking': False}, 'terms': {}}
    for i in xrange(0,queryset.count()):
        serie = {'options': {
                 'source': ProductPageRank.objects.filter
                    (keyword=queryset[i]['keyword'], created__gt=dt_f, created__lt=dt_t, item_id=item_id)},
                 'terms': [{'created'+str(i):'created'}, {queryset[i]['keyword']: 'rank'}],
        }
        series.append(serie)
        series_option['terms'].update({'created'+str(i):[queryset[i]['keyword']]})

    productpagerankdata = DataPool(series=series)

    def mapf(*t):
        ts = long(time.mktime(time.strptime(t[0], "%Y-%m-%d %H:%M")))*1000
        return (ts,)

    productpagerankcht = Chart(
            datasource=productpagerankdata,
            series_options=[series_option],
            #x_sortf_mapf_mts=(None,mapf,True),
            chart_options=
                {'chart': {'renderTo': "container" + str(index)},
                 'title': {
                     'text': u'\u67e5\u8be2\u5546\u54c1ID\uff1a%s' % (item_id)},
                 'xAxis': {'title': {'text': 'per half hour'},'type': 'string',
                           'labels':{'rotation': -45,'align':'right','style': {'font': 'normal 12px Verdana, sans-serif'}}},
                 'yAxis': {
                     'title': {'text': 'ranks'},
                     'min': 0,
                     'minorGridLineWidth': 0,
                     'gridLineWidth': 0,
                     'alternateGridColor': None,
                     },
                 'plotOptions': {
                     'spline': {
                         'lineWidth': 1, 'states': {'hover': {'lineWidth': 2}},
                         'marker': {
                             'enabled': False,
                             'states':{'hover':{'enabled':True,'symbol':'cycle','radius':0,'lineWidth':1}}
                             },
                         },
                         #'pointInterval':3600000,
                         #'pointStart':1330531200
                     },
                 })

    return productpagerankcht

def genItemKeywordsRankChart(request, dt_f, dt_t):

    item_ids = request.GET.get('item_ids')

    item_ids = item_ids.split(',')
    pagerankchts = []

    for item_id in item_ids:
        index = len(pagerankchts) + 1
        cht = getItemKeywordsChart(item_id, dt_f, dt_t, index)
        if cht:
            pagerankchts.append(cht)

    if not pagerankchts:
        return HttpResponse('item_ids is not avalible .')

    rankqueryset = ProductPageRank.objects.filter(item_id__in = item_ids)\
        .values('item_id', 'nick', 'title').distinct('item_id')

    for item in  rankqueryset:
        try:
            product = ProductItem.objects.get(num_iid=item['item_id'])
            item['pic_url'] = product.pic_url
        except:
            pass

    params = {'keywordsrankcharts': pagerankchts, 'items': rankqueryset}

    return render_to_response('item_keywordsrank.html', params, context_instance=RequestContext(request))


def getPageRankPivotChart(nick, keyword, dt_f, dt_t, index):
    serie = {'options': {
        'source': ProductPageRank.objects.filter
                (nick=nick, keyword=keyword, created__gt=dt_f, created__lt=dt_t),
        'categories': ['month', 'day'],
        'legend_by': 'item_id',
        #'top_n_per_cat':3
        },
        'terms': {
         'avg_rank': Avg('rank'),
         'variance_rank': {'func': Variance('rank'), 'legend_by': 'item_id'},
        }
    }

    productpagerankpivotdata = PivotDataPool(series=[serie])

    productpagerankpivcht =\
    PivotChart(
            datasource=productpagerankpivotdata,
            series_options=
            [{'options': {
                'type': 'line',
                'stacking': False},
              'terms': ['avg_rank', {'variance_rank': {'type': 'column', 'yAxis': 1}}]}, ],
            chart_options=
                {'chart': {'renderTo': "container" + str(index), 'zoomType': 'xy'},
                 'title': {'text': '%s-%s' % (nick.encode('utf8'), keyword.encode('utf8'))},
                 'xAxis': {'title': {'text': 'Month&Day'},
                           'labels':{'rotation': -45,'align':'right',
                                   'style': {'font': 'normal 12px Verdana, sans-serif'}}},
                 'yAxis': [{'title': {'text': 'rank avg'}}, {'title': {'text': 'rank variance'}, 'opposite': True}]
                 }
            )

    return productpagerankpivcht

def genPageRankPivotChart(request, dt_f, dt_t):
    nicks = request.GET.get('nicks')
    keywords = request.GET.get('keywords', None)

    nicks_list = nicks.split(',')
    if not keywords:
        keys = request.user.get_profile().craw_keywords
        keywords_list = keys.split(',') if keys else []
    else:
        keywords_list = keywords.split(',')

    pagerankchts = []

    for keyword in keywords_list:
        for nick in nicks_list:
            index = len(pagerankchts) + 1
            cht = getPageRankPivotChart(nick, keyword, dt_f, dt_t, index)
            if cht:
                pagerankchts.append(cht)

    if not pagerankchts:
        return HttpResponse('nick is not avalible under this keyword.')

    rankqueryset = ProductPageRank.objects.filter\
            (nick__in=nicks_list, keyword__in=keywords_list, created__gt=dt_f, created__lt=dt_t)\
    .values('item_id', 'nick', 'title').distinct('item_id')

    for item in  rankqueryset:
        try:
            product = ProductItem.objects.get(num_iid=item['item_id'])
            item['pic_url'] = product.pic_url
        except:
            pass

    params = {'keywordsrankcharts': pagerankchts, 'items': rankqueryset}

    return render_to_response('keywords_rankstatistic.html', params, context_instance=RequestContext(request))



def getItemAvgRankPivotChart(nick,dt_f, dt_t,index):
    serie = {'options': {
        'source': ProductPageRank.objects.filter
                (nick=nick, created__gt=dt_f, created__lt=dt_t),
        'categories': ['month', 'day'],
        'legend_by': 'item_id',
        #'top_n_per_cat':3
        },
        'terms': {
         'avg_rank': Avg('rank'),
        }
    }

    productpagerankpivotdata = PivotDataPool(series=[serie])

    productpagerankpivcht = PivotChart(
        datasource=productpagerankpivotdata,
        series_options=[{'options': {
            'type': 'line',
            'stacking': False},
          'terms': ['avg_rank']}, ],
        chart_options={'chart': {'renderTo': "container"+str(index), 'zoomType': 'xy'},
             'title': {'text': '%s' % (nick.encode('utf8'))},
             'xAxis': {'title': {'text': 'Month&Day'},
                       'labels':{'rotation': -45,'align':'right',
                                 'style': {'font': 'normal 12px Verdana, sans-serif'}}},
             'yAxis': [{'title': {'text': 'rank avg'}}]
        }
    )

    return productpagerankpivcht

def genItemAvgRankPivotChart(request, dt_f, dt_t):
    nicks = request.GET.get('nicks')
    nicks_list = nicks.split(',')

    pagerankchts = []

    for nick in nicks_list:
        index = len(pagerankchts) + 1
        cht = getItemAvgRankPivotChart(nick,dt_f, dt_t,index)
        if cht:
            pagerankchts.append(cht)

    if not pagerankchts:
        return HttpResponse('nick is not avalible under this keyword.')

    rankqueryset = ProductPageRank.objects.filter(nick__in=nicks_list,created__gt=dt_f, created__lt=dt_t)\
               .values('item_id', 'nick', 'title').distinct('item_id')

    for item in  rankqueryset:
        try:
            product = ProductItem.objects.get(num_iid=item['item_id'])
            item['pic_url'] = product.pic_url
        except:
            pass

    params = {'keywordsrankcharts': pagerankchts, 'items': rankqueryset}

    return render_to_response('keywords_rankstatistic.html', params, context_instance=RequestContext(request))


####################################### Trade views #######################################

def getTradePeroidChart(request,dt_f,dt_t):
    nicks = request.GET.get('nicks',None)
    cat_by = request.GET.get('cat_by','hour')
    xy = request.GET.get('xy','horizontal')

    nicks_list = nicks.split(',')

    queryset = ProductTrade.objects.filter(trade_at__gte=dt_f,trade_at__lt=dt_t)\
        .filter(nick__in = nicks_list)

    if queryset.count() == 0:
        return HttpResponse('No data for these nick!')

    if xy == 'vertical':
        categories = [cat_by]
    else:
        if cat_by == 'month':
            categories = ['month']
        elif cat_by == 'day':
            categories = ['month','day']
        elif cat_by == 'week':
            categories = ['week']
        else :
            categories = ['month','day','hour']


    series = {'options': {
           'source': queryset,
           'categories': categories,
           'legend_by': 'nick'},
           'terms': {'total_num':Sum('num'),'total_sales':{'func':Sum('price'),'legend_by':'nick'}}}

    def mapf(*t):
        names ={0:'0',1: '01', 2: '02', 3: '03', 4: '04',
                5: '05', 6: '06', 7: '07', 8: '08',9: '09'}
        num = t[0]
        l = list(num)
        ret = []
        for s in l:
            if int(s)<10:
                s = names[int(s)]
            ret.append(s)
        return tuple(ret)

    ordersdata = PivotDataPool(series=[series],sortf_mapf_mts=(None,mapf,True))

    series_options =[{'options':{'type': 'column','stacking': True,'yAxis': 0},
                      'terms':['total_num',{'total_sales':{'type':'line','stacking':False,'yAxis':1}}]},]
    ordersdatacht = PivotChart(
            datasource = ordersdata,
            series_options = series_options,
            chart_options =
              { 'chart':{'zoomType': 'xy'},
                'title': {'text': nicks},
                'xAxis': {'title': {'text': 'per %s'%(cat_by)},
                          'labels':{'rotation': -45,'align':'right',
                                   'style': {'font': 'normal 12px Verdana, sans-serif'}}},
                'yAxis': [{'title': {'text': 'total num '}},{'title': {'text': 'total sales'},'opposite': True}]})

    params = {'ordersdatacht':ordersdatacht}


    return render_to_response('hourly_ordernumschart.html',params,context_instance=RequestContext(request))


def getTradePivotChart(request,dt_f,dt_t):

    seller_num = int(request.GET.get('seller_num',20))
    type = request.GET.get('sort_by','total_nums')

    queryset = ProductTrade.objects.filter(trade_at__gte=dt_f,trade_at__lt=dt_t)

    if queryset.count() == 0:
        return HttpResponse('No data for these nick!')

    series = {'options': {'source': queryset,'categories': ['user_id',]},
           'terms': {'total_nums':Sum('num'),'total_sales':{'func':Sum('price')},},
    }

    def mapf(*t):
        key = t[0][0]
        nick = ProductTrade.objects.filter(user_id=key)[0].nick
        return (nick,)

    ordersdata = PivotDataPool(series=[series],top_n=seller_num,top_n_term=type
                               ,pareto_term=type,sortf_mapf_mts=(None,mapf,True))

    series_options =[{'options':{'type': 'column','yAxis': 0},
                      'terms':['total_nums',{'total_sales':{'type':'column','stacking':False,'yAxis':1}}]},]
    ordersdatacht = PivotChart(
            datasource = ordersdata,
            series_options = series_options,
            chart_options =
              { 'chart':{'zoomType': 'xy'},
                'title': {
                    'text':u'\u9500\u552e\u91cf\u53ca\u9500\u552e\u989d\u6392\u524d%s\u7684\u5356\u5bb6\u6570\u636e'
                      %seller_num},
                'xAxis': {'title': {'text': 'total nums & sales'},
                          'labels':{'rotation': -45,'align':'right',
                                   'style': {'font': 'normal 12px Verdana, sans-serif'}}},
                'yAxis': [{'title': {'text': 'total nums '}},{'title': {'text': 'total sales'},'opposite': True},],})

    params = {'ordersdatacht':ordersdatacht}

    return render_to_response('hourly_ordernumschart.html',params,context_instance=RequestContext(request))






  