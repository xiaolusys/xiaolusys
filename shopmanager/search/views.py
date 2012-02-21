import time
import datetime
import json
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db.models import Avg
from django.template import RequestContext
from chartit import DataPool, Chart
from chartit import PivotDataPool, PivotChart
from search.scrawurldata import getTaoBaoPageRank,getCustomShopsPageRank
from search.models import ProductPageRank
from auth.utils import parse_datetime,format_time
from search.tasks import keywords
from search.tasks import keywords as task_keywords
from shopback.base.aggregates import ConcatenateDistinct

def getShopsRank(request):

    nicks = request.GET.get('nicks',None)
    keywords = request.GET.get('keywords',None)
    page_nums = int(request.GET.get('page_nums','5'))

    if not nicks and not keywords:
        return HttpResponse('nicks and keywords can\'t be empty!')

    nicks = nicks.split(',')
    keywords = keywords.split(',')

    results = getCustomShopsPageRank(nicks,keywords,page_nums)

    strings =''
    for keyword,nicks_result in  results.iteritems():

        for nick,values in nicks_result.iteritems():

            strings += keyword.encode('utf8')+'---------'+nick.encode('utf8')+'<br>'

            for value in values:
                strings += value['title'].encode('utf8')+'======='+str(value['rank'])+'<br>'

    return HttpResponse(strings)



def getProductPeriodChart(nick,keyword,dt_f,dt_t,index):

    rankqueryset = ProductPageRank.objects.filter(nick=nick,keyword=keyword,created__gt=dt_f,created__lt=dt_t)\
                   .values('item_id','title').distinct('item_id')

    if rankqueryset.count() == 0:
        return None

    series = []
    series_option ={'options':{'type':'spline','stacking': False},'terms':{}}
    for prod in rankqueryset:

        serie ={'options': {
               'source': ProductPageRank.objects.filter(keyword=keyword,created__gt=dt_f,created__lt=dt_t,item_id=prod['item_id'])},
               'terms': [{'created'+prod['item_id']:'created'},{prod['item_id']:'rank'}]}
        series.append(serie)
        series_option['terms'].update({'created'+prod['item_id']:[prod['item_id']]})


    productpagerankdata = DataPool(series=series)

    productpagerankcht = Chart(
            datasource = productpagerankdata,
            series_options = [series_option],
            chart_options =
              { 'chart': {'renderTo':"container"+str(index)},
                'title': {
                   'text': '%s-%s'%(nick.encode('utf8'),keyword.encode('utf8'))},
                'xAxis': {'title': {'text': 'per half hour'},'type':'string'},
                'yAxis': {
                    'title': {'text': 'ranks'},
                    'min':0,
                    'minorGridLineWidth':0,
                    'gridLineWidth':0,
                    'alternateGridColor':None,
                    'plotBands':[
                        {'from': 0,'to': 40,'color': 'rgba(68, 170, 213, 0.1)',
                         'label': {'text': 'page 1','style': {'color': '#606060'}}},
                        {'from': 40,'to': 80,'color': 'rgba(170, 190, 35, 0.2)',
                         'label': {'text': 'page 2','style': {'color': '#2A78CB'}}},
                        {'from': 80,'to': 120,'color': 'rgba(68, 170, 213, 0.1)',
                         'label': {'text': 'page 3','style': {'color': '#606060'}}},
                        {'from': 120,'to': 160,'color': 'rgba(170, 190, 35, 0.2)',
                         'label': {'text': 'page 4','style': {'color': '#2A78CB'}}},
                        {'from': 160,'to': 200,'color': 'rgba(68, 170, 213, 0.1)',
                         'label': {'text': 'page 5','style': {'color': '#606060'}}},
                        {'from': 200,'to': 240,'color': 'rgba(170, 190, 35, 0.2)',
                         'label': {'text': 'page 6','style': {'color': '#2A78CB'}}},
                    ]
                },
                'plotOptions': {
                    'spline': {
                        'lineWidth': 1,'states': {'hover': {'lineWidth': 2 }},
                            'marker': {
                                    'enabled': False,
                                    'states': {
                                        'hover': {
                                            'enabled': True,
                                            'symbol': 'circle',
                                            'radius': 5,
                                            'lineWidth': 1
                                        }
                                    }
                            },
                    },
                },
            })


    return productpagerankcht



def genPeriodChart(request,dt_f,dt_t):

    nicks = request.GET.get('nicks')
    keywords = request.GET.get('keywords',None)

    nicks_list = nicks.split(',')
    if not keywords:
        keywords_list = task_keywords
    else:
        keywords_list = keywords.split(',')

    pagerankchts = []

    for keyword in keywords_list:
        for nick in nicks_list:

            index = len(pagerankchts)+1
            cht = getProductPeriodChart(nick,keyword,dt_f,dt_t,index)
            if cht:
                pagerankchts.append(cht)

    if not pagerankchts:
        return HttpResponse('nick is not avalible under this keyword.')

    rankqueryset = ProductPageRank.objects.filter(nick__in =nicks_list,keyword__in=keywords_list,created__gt=dt_f,created__lt=dt_t)\
        .values('item_id','nick','title').distinct('item_id')

    params = {'keywordsrankcharts': pagerankchts,'items':rankqueryset}


    return render_to_response('keywords_itemsrank.html',params,context_instance=RequestContext(request))


def genPageRankPivotChart(request,dt_f,dt_t):

    nick = request.GET.get('nick',None)
    keyword = request.GET.get('keyword',None)


    dt_f = datetime.datetime(*(time.strptime(dt_f, '%Y-%m-%d')[0:6]))
    dt_t = datetime.datetime(*(time.strptime(dt_t, '%Y-%m-%d')[0:6]))

    f_month = dt_f.month-1
    f_day = dt_f.day-1

    t_month = dt_t.month+1
    t_day = dt_t.day+1

    serie = {'options': {
               'source': ProductPageRank.objects.filter
                       (nick=nick,keyword=keyword,month__gt=f_month,month__lt=t_month,day__gt=f_day,day__lt=t_day),
               'categories': ['month','day'],
               'legend_by':'item_id',
               #'top_n_per_cat':3
                       },
              'terms': {
                'avg_rank': Avg('rank'),
                }}

    rankqueryset = ProductPageRank.objects.filter\
            (nick=nick,keyword=keyword,month__gt=f_month,month__lt=t_month,day__gt=f_day,day__lt=t_day)\
            .values('item_id','title').distinct('item_id')


    productpagerankpivotdata = PivotDataPool(series =[serie])

    productpagerankpivcht = \
        PivotChart(
            datasource = productpagerankpivotdata,
            series_options =
              [{'options':{
                  'type': 'line',
                  'stacking': False},
                'terms':['avg_rank']}],
            chart_options =
              {'title': {
                   'text': 'Items Avg Rank By Day'},
               'xAxis': {
                    'title': {
                       'text': 'Month&Day'}},
               'yAxis': {
                    'title': {
                       'text': 'rank'}}})

    params = {'keywordsrankchart':productpagerankpivcht,'items':rankqueryset,'nick':nick,'keyword':keyword}

    return render_to_response('keywords_itemsrank.html',params,context_instance=RequestContext(request))




  