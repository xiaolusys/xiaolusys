import re
import json
import datetime
from subway.models import Hotkey, KeyScore

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def saveHotkeys(request):
    SRH_WRD=1; SRH_PPL=2; SRH_TMS=3; CLK_TMS=4; MAL_CLK=5; CML_CLK=6; NUM_TRD=8; PRICE=10

    datatype = request.POST.get("type")
    keystr = request.POST.get("hotkeys")
    
    if datatype == "search":
        SRH_PPL=7; SRH_TMS=2; SRH_CRT =10;PRICE=11;

    keys = json.loads(keystr)
    dt = datetime.datetime.now()
    today_end = datetime.datetime(dt.year,dt.month,dt.day,23,59,59)


    n = keys[0][-1]
    for i in range(0,n):
        item = keys[0][i]
        try:
            exist_item = Hotkey.objects.get(word=item[SRH_WRD])

            timedel = today_end - exist_item.updated
            if timedel.days > 1:
                exist_item.num_people=item[SRH_PPL]
                exist_item.num_search=item[SRH_TMS]
                exist_item.num_click=item[CLK_TMS]
                exist_item.num_tmall_click=item[MAL_CLK]
                exist_item.num_cmall_click=item[CML_CLK]
                exist_item.num_trade=item[NUM_TRD] if datatype != 'search' else item[SRH_TMS]*float(item[SRH_CRT])
                exist_item.ads_price_cent=item[PRICE]*100
                exist_item.save()

        except Hotkey.DoesNotExist:
            Hotkey.objects.create(
                word=item[SRH_WRD],num_people=item[SRH_PPL],
                num_search=item[SRH_TMS],num_click=item[CLK_TMS],
                num_tmall_click=item[MAL_CLK],num_cmall_click=item[CML_CLK],
                num_trade=item[NUM_TRD] if datatype != 'search' else item[SRH_TMS]*float(item[SRH_CRT])
                ,ads_price_cent=item[PRICE]*100)


    return HttpResponse(json.dumps({"code":0}))

@csrf_exempt
def saveKeyScores(request):

    keystr = request.POST.get('keyscores')

    item_ks = json.loads(keystr)
    num_iid = item_ks.get('num_iid',None)
    keyscores = item_ks.get('keyscores',None)

    if not (num_iid and keyscores):
        return HttpResponse(json.dumps({"code":1,"error":"Num_iid and keyscores can't be null."}))

    dt = datetime.datetime.now()
    today_end = datetime.datetime(dt.year,dt.month,dt.day,23,59,59)

    for ks in keyscores:
        try:
            hotkey = Hotkey.objects.get(word=ks[0])
        except Hotkey.DoesNotExist:
            continue

        try:
            ks_ins = KeyScore.objects.get(num_iid=num_iid,hotkey=hotkey)
            timedel = today_end - ks_ins.updated
            if timedel.days > 1:
                ks_ins.score = ks[1]
                ks_ins.save()
        except KeyScore.DoesNotExist:
            KeyScore.objects.create(num_iid=num_iid,hotkey=hotkey,score=ks[1])

    return HttpResponse(json.dumps({"code":0}))


def getValuableHotKeys(request):
    type = request.GET.get("type", None)
    num_iid  = request.GET.get("num_iid", None)
    num_keys = int(request.GET.get("num", 20))

    if num_iid is None:
        return HttpResponse(json.dumps({"code": 1, "error": "no product id"}))

    sort_by = ''
    sort_ratio_by = ''
    if type == 'A':
        sort_by = 'hotkey__num_people'
    elif type == 'B':
        sort_by = 'hotkey__num_search'
    elif type == 'C':
        sort_by = 'hotkey__num_click'
    elif type == 'D':
        sort_by = 'hotkey__num_tmall_click'
    elif type == 'E':
        sort_by = 'hotkey__num_cmall_click'
    elif type == 'F':
        sort_by = 'hotkey__num_trade'
    elif type == 'G':
        sort_ratio_by = 'ads_price'
    elif type == 'C/B':
        sort_ratio_by = 'click_ratio'
    elif type == 'E/B':
        sort_ratio_by = 'cmall_click_ratio'
    elif type == 'F/B':
        sort_ratio_by = 'trade_search_ratio'
    elif type == 'F/C':
        sort_ratio_by = 'trade_click_ratio'
    else :
        return HttpResponse(json.dumps({"code":1,"error":'Search type is not in Supplied type!'}))

    hot_keyscores = KeyScore.objects.filter(num_iid=num_iid)
    if sort_by:
        hot_keyscores = hot_keyscores.order_by('-'+sort_by).values(sort_by,'num_iid','score','hotkey__word')[:num_keys]
        hot_keyscores = [hks for hks in hot_keyscores]
    elif sort_ratio_by:

        def sortIndex(sort_key,key_value,sort_list):
            i = -1
            for i in xrange(0,len(sort_list)):
                if sort_list[i][sort_key]>=key_value:
                    continue
                return i
            return i+1

        hot_ks_dc = []
        for hks in hot_keyscores:
            hot_ks = {}
            hot_ks[sort_ratio_by]  = eval('hks.hotkey.'+sort_ratio_by)
            hot_ks['num_iid']      = hks.num_iid
            hot_ks['hotkey__word'] = hks.hotkey.word
            hot_ks['score']        = hks.score
            index = sortIndex(sort_ratio_by,hot_ks[sort_ratio_by],hot_ks_dc)
            hot_ks_dc.insert(index,hot_ks)
        hot_keyscores = hot_ks_dc[:num_keys]

    return HttpResponse(json.dumps({"code":0,"response_content":hot_keyscores}))
    
    
