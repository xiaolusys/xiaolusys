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
from auth.utils import parse_datetime

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


def genPeroidChart(request):

    nick = request.GET.get('nick',None)
    keyword = request.GET.get('keyword',None)
    dt = request.GET.get('dt',None)

    if not dt:
        dt = datetime.datetime.now()
    else :
        dt = datetime.datetime(*(time.strptime(dt, '%Y-%m-%d')[0:6]))

    month = dt.month
    day = dt.day

    rankqueryset = ProductPageRank.objects.filter(nick=nick,keyword=keyword,day=day,month=month)\
                   .values('item_id','title').distinct('item_id')

    if rankqueryset.count() == 0:
        return HttpResponse('no items under this keyword or this day')

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

    params = {'keywordsrankchart': productpagerankcht,'items':rankqueryset,'nick':nick,'keyword':keyword}


    return render_to_response('keywords_itemsrank.html',params,context_instance=RequestContext(request))


def genPageRankPivotChart(request):

    productpagerankpivotdata = \
        PivotDataPool(
           series =
            [{'options': {
               'source': ProductPageRank.objects.all(),
               'categories': ['month']},
               'legend_by':['state','city'],
               'top_n_per_cat':3,
              'terms': {
                'avg_rain': Avg('rainfall'),
                }}
             ])

    productpagerankpivcht = \
        PivotChart(
            datasource = productpagerankpivotdata,
            series_options =
              [{'options':{
                  'type': 'column',
                  'stacking': True},
                'terms':['avg_rain']}],
            chart_options =
              {'title': {
                   'text': 'Rain by Month in top 3 cities'},
               'xAxis': {
                    'title': {
                       'text': 'Month'}}})

    return HttpResponse('ok')




  