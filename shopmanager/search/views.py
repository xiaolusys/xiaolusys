import time
import datetime
import json
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db.models import Avg,Variance
from django.template import RequestContext
from chartit import DataPool, Chart
from chartit import PivotDataPool, PivotChart
from search.scrawurldata import getTaoBaoPageRank,getCustomShopsPageRank
from search.models import ProductPageRank
from auth.utils import parse_datetime,format_time
from autolist.models import ProductItem
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
                strings += value['item_id']+'===='+value['title'].encode('utf8')+'======='+str(value['rank'])+'<br>'

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
#                    'plotBands':[
#                        {'from': 0,'to': 40,'color': 'rgba(0, 255, 0, 0.1)',
#                         'label': {'text': 'page 1','style': {'color': '#606060'}}},
#                        {'from': 40,'to': 80,'color': 'rgba(170, 190, 35, 0.2)',
#                         'label': {'text': 'page 2','style': {'color': '#2A78CB'}}},
#                        {'from': 80,'to': 120,'color': 'rgba(68, 170, 213, 0.1)',
#                         'label': {'text': 'page 3','style': {'color': '#606060'}}},
#                        {'from': 120,'to': 160,'color': 'rgba(170, 190, 35, 0.2)',
#                         'label': {'text': 'page 4','style': {'color': '#2A78CB'}}},
#                        {'from': 160,'to': 200,'color': 'rgba(68, 170, 213, 0.1)',
#                         'label': {'text': 'page 5','style': {'color': '#606060'}}},
#                        {'from': 200,'to': 240,'color': 'rgba(170, 190, 35, 0.2)',
#                         'label': {'text': 'page 6','style': {'color': '#2A78CB'}}},
#                    ]
                },
                'plotOptions': {
                    'spline': {
                        'lineWidth': 1,'states': {'hover': {'lineWidth': 2 }},
                            'marker': {
                                    'enabled': False,
                                    'states': {
                                        'hover': {
                                            'enabled': True,
                                            'symbol': 'cycle',
                                            'radius': 0,
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

    for item in  rankqueryset:
        try:
            product =  ProductItem.objects.get(num_iid=item['item_id'])
            item['pic_url'] = product.pic_url
        except :
            pass


    params = {'keywordsrankcharts': pagerankchts,'items':rankqueryset}


    return render_to_response('keywords_itemsrank.html',params,context_instance=RequestContext(request))


def getPageRankPivotChart(nick,keyword,dt_f,dt_t,index):

    serie = {'options': {
               'source': ProductPageRank.objects.filter
                       (nick=nick,keyword=keyword,created__gt=dt_f,created__lt=dt_t),
               'categories': ['month','day'],
               'legend_by':'item_id',
               #'top_n_per_cat':3
                       },
              'terms': {
                'avg_rank': Avg('rank'),
                'variance_rank':{'func':Variance('rank'),'legend_by':'item_id'},
                }}

    productpagerankpivotdata = PivotDataPool(series =[serie])

    productpagerankpivcht = \
        PivotChart(
            datasource = productpagerankpivotdata,
            series_options =
              [{'options':{
                  'type': 'line',
                  'stacking': False},
                'terms':['avg_rank',{'variance_rank':{'type':'column','yAxis':1}}]},],
            chart_options =
              { 'chart': {'renderTo':"container"+str(index),'zoomType': 'xy'},
                'title': {'text': '%s-%s'%(nick.encode('utf8'),keyword.encode('utf8'))},
                'xAxis': {'title': {'text': 'Month&Day'}},
                'yAxis':[{},{'opposite': True}]
               })

    return productpagerankpivcht

def genPageRankPivotChart(request,dt_f,dt_t):

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
            cht = getPageRankPivotChart(nick,keyword,dt_f,dt_t,index)
            if cht:
                pagerankchts.append(cht)

    if not pagerankchts:
        return HttpResponse('nick is not avalible under this keyword.')

    rankqueryset = ProductPageRank.objects.filter\
            (nick__in=nicks_list,keyword__in=keywords_list,created__gt=dt_f,created__lt=dt_t)\
            .values('item_id','nick','title').distinct('item_id')

    for item in  rankqueryset:
        try:
            product =  ProductItem.objects.get(num_iid=item['item_id'])
            item['pic_url'] = product.pic_url
        except :
            pass

    params = {'keywordsrankcharts':pagerankchts,'items':rankqueryset}

    return render_to_response('keywords_itemsrank.html',params,context_instance=RequestContext(request))




  