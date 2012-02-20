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



def getProductPeriodChart(nick,keyword,month,day):

    rankqueryset = ProductPageRank.objects.filter(nick=nick,keyword=keyword,day=day,month=month)\
                   .values('item_id','title').distinct('item_id')

    if rankqueryset.count() == 0:
        return None

    series = []
    series_option ={'options':{'type': 'line','stacking': False},'terms':{}}
    for prod in rankqueryset:

        serie ={'options': {
               'source': ProductPageRank.objects.filter(keyword=keyword,day=day,month=month,item_id=prod['item_id'])},
               'terms': [{'time'+prod['item_id']:'time'},{prod['item_id']:'rank'}]}
        series.append(serie)
        series_option['terms'].update({'time'+prod['item_id']:[prod['item_id']]})


    productpagerankdata = DataPool(series=series)

    productpagerankcht = Chart(
            datasource = productpagerankdata,
            series_options = [series_option],
            chart_options =
              {'title': {
                   'text': '%s'%(keyword.encode('utf8'))},
               'xAxis': {
                    'title': {
                       'text': 'per half hour'}}})

    return productpagerankcht


def genPeroidChart(request):

    nick = request.GET.get('nick',u'\u4f18\u5c3c\u5c0f\u5c0f\u4e16\u754c')
    dt = request.GET.get('dt',None)
    keyword = request.GET.get('keyword',None)

    if not dt:
        dt = datetime.datetime.now()
    else :
        dt = datetime.datetime(*(time.strptime(dt, '%Y-%m-%d')[0:6]))

    month = dt.month
    day = dt.day

    productpagerankcht = getProductPeriodChart(nick,keyword,month,day)

    if not productpagerankcht:
        return HttpResponse('nick is not avalible under this keyword.')

    rankqueryset = ProductPageRank.objects.filter(nick=nick,day=day,month=month)\
        .values('item_id','title').distinct('item_id')

    params = {'keywordsrankcharts': productpagerankcht,'items':rankqueryset,'nick':nick}


    return render_to_response('keywords_itemsrank.html',params,context_instance=RequestContext(request))


#def getProductPeriodChart(nick,keyword,f_month,f_day,t_month,t_day):
#
#    rankqueryset = ProductPageRank.objects.filter\
#            (nick=nick,keyword=keyword,month__gt=f_month,month__lt=t_month,day__gt=f_day,day__lt=t_day)\
#                   .values('item_id','title').distinct('item_id')
#
#    if rankqueryset.count() == 0:
#        return None
#
#    series = []
#    series_option ={'options':{'type': 'line','stacking': False},'terms':{}}
#    for prod in rankqueryset:
#
#        serie ={'options': {
#               'source': ProductPageRank.objects.filter
#                       (keyword=keyword,month__gt=f_month,month__lt=t_month,day__gt=f_day,day__lt=t_day,item_id=prod['item_id'])
#                       .aggregate()
#                    },
#               'terms': [{'time'+prod['item_id']:'time'},{prod['item_id']:'rank'}]}
#        series.append(serie)
#        series_option['terms'].update({'time'+prod['item_id']:[prod['item_id']]})
#
#
#    productpagerankdata = DataPool(series=series)
#
#    productpagerankcht = Chart(
#            datasource = productpagerankdata,
#            series_options = [series_option],
#            chart_options =
#              {'title': {
#                   'text': '%s'%(keyword.encode('utf8'))},
#               'xAxis': {
#                    'title': {
#                       'text': 'per half hour'}},
#               'yAxis': {
#                    'title': {
#                       'text': 'rank'}}})
#
#
#    return productpagerankcht
#
#def genPeroidChart(request,dt_f,dt_t):
#
#    nick = request.GET.get('nick',u'\u4f18\u5c3c\u5c0f\u5c0f\u4e16\u754c')
#
#    dt_f = datetime.datetime(*(time.strptime(dt_f, '%Y-%m-%d')[0:6]))
#    dt_t = datetime.datetime(*(time.strptime(dt_t, '%Y-%m-%d')[0:6]))
#
#    f_month = dt_f.month-1
#    f_day = dt_f.day-1
#
#    t_month = dt_t.month+1
#    t_day = dt_t.day+1
#
#    productpagerankchts = []
#
#    for keyword in keywords:
#        chts = getProductPeriodChart(nick,keyword,f_month,f_day,t_month,t_day)
#        if chts:
#            productpagerankchts.append(chts)
#    print productpagerankchts
#    rankqueryset = ProductPageRank.objects.filter(nick=nick,month__gt=f_month,month__lt=t_month,day__gt=f_day,day__lt=t_day)\
#        .values('item_id','title').distinct('item_id')
#
#    params = {'keywordsrankcharts': productpagerankchts,'items':rankqueryset,'nick':nick}
#
#
#    return render_to_response('keywords_itemsrank.html',params,context_instance=RequestContext(request))


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




  