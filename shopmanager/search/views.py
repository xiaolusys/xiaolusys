import json
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.db.models import Avg
from chartit import DataPool, Chart
from chartit import PivotDataPool, PivotChart
from search.scrawurldata import getTaoBaoPageRank,getCustomShopsPageRank
from search.models import ProductPageRank

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

    keyword = '\xe7\x9d\xa1\xe8\xa2\x8b \xe5\x84\xbf\xe7\xab\xa5 \xe9\x98\xb2\xe8\xb8\xa2\xe8\xa2\xab'
    title = '\xe4\xbc\x98\xe5\xb0\xbc\xe4\xb8\x96\xe7\x95\x8c \xe5\xae\x9d\xe5\xae\x9d\xe7\x9d\xa1\xe8\xa2\x8b \
             \xe5\xa9\xb4\xe5\x84\xbf\xe7\x9d\xa1\xe8\xa2\x8b \xe5\x84\xbf\xe7\xab\xa5\xe9\x98\xb2\xe8\xb8\xa2\xe8\xa2\xab \
             \xe5\xa4\xa7\xe7\xab\xa5\xe6\x98\xa5\xe7\xa7\x8b\xe5\x86\xac\xe6\xac\xbe\xe5\x8a\xa0\xe5\x8e\x9a\xe5\x8a\xa0\xe9\x95\xbf'

    productpagerankdata = \
        DataPool(
           series=
            [{'options': {
               'source': ProductPageRank.objects.all(keyword=keyword,titile=title)},
               'terms': ['title','search_datetime','rank']}
             ])

    productpagerankcht = Chart(
            datasource = productpagerankdata,
            series_options =
              [{'options':{
                  'type': 'line',
                  'stacking': False},
                'terms':{
                  'search_datetime': ['rank']
                  }}],
            chart_options =
              {'title': {
                   'text': '%s,%s'(keyword,title)},
               'xAxis': {
                    'title': {
                       'text': 'date time'}}})

#    productpagerankpivotdata = \
#        PivotDataPool(
#           series =
#            [{'options': {
#               'source': ProductPageRank.objects.all(),
#               'categories': ['month']},
#               'legend_by':['state','city'],
#               'top_n_per_cat':3,
#              'terms': {
#                'avg_rain': Avg('rainfall'),
#                }}
#             ])
#
#    productpagerankpivcht = \
#        PivotChart(
#            datasource = productpagerankpivotdata,
#            series_options =
#              [{'options':{
#                  'type': 'column',
#                  'stacking': True},
#                'terms':['avg_rain']}],
#            chart_options =
#              {'title': {
#                   'text': 'Rain by Month in top 3 cities'},
#               'xAxis': {
#                    'title': {
#                       'text': 'Month'}}})

    return render_to_response('keywords_itemsrank.html',{'keywordsrankchart': productpagerankcht})




  