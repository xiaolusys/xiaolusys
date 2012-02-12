import json
from django.http import HttpResponse
from search.scrawurldata import getTaoBaoPageRank,getCustomShopsPageRank

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



  