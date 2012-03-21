import re
import json
import datetime
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from subway.models import Hotkey, KeyScore
from autolist.models import ProductItem
from auth.utils import unquote



@csrf_exempt
def saveHotkeys(request):
    SRH_WRD=1; SRH_PPL=2; SRH_TMS=3; CLK_TMS=4; MAL_CLK=5; CML_CLK=6; NUM_TRD=8; PRICE=10

    keystr = request.POST.get("hotkeys")
    cat_id = request.POST.get("cat_id")

    product_items = ProductItem.objects.all()
    if not cat_id:
        SRH_PPL=7; SRH_TMS=2; SRH_CRT =10;PRICE=11;
    else:
        product_items = product_items.filter(category_id=cat_id)

    keys = json.loads(keystr)
    dt = datetime.datetime.now()
    today_end = datetime.datetime(dt.year,dt.month,dt.day,23,59,59)

    n = keys[0][-1]
    for i in range(0,n):
        item = keys[0][i]
        try:
            hotkey_item = Hotkey.objects.get(word=item[SRH_WRD],category_id=cat_id)

            timedel = today_end - hotkey_item.updated
            if timedel.days > 1:
                hotkey_item.num_people=item[SRH_PPL]
                hotkey_item.num_search=item[SRH_TMS]
                hotkey_item.num_click=item[CLK_TMS]
                hotkey_item.num_tmall_click=item[MAL_CLK]
                hotkey_item.num_cmall_click=item[CML_CLK]
                hotkey_item.num_trade=item[NUM_TRD] if cat_id else item[SRH_TMS]*float(item[SRH_CRT])
                hotkey_item.category_id= cat_id if cat_id else ''
                hotkey_item.ads_price_cent=item[PRICE]*100
                hotkey_item.save()

        except Hotkey.DoesNotExist:
            hotkey_item = Hotkey.objects.create(
                word=item[SRH_WRD],num_people=item[SRH_PPL],
                num_search=item[SRH_TMS],num_click=item[CLK_TMS],
                num_tmall_click=item[MAL_CLK],num_cmall_click=item[CML_CLK],
                num_trade=item[NUM_TRD] if cat_id else item[SRH_TMS]*float(item[SRH_CRT])
                ,ads_price_cent=item[PRICE]*100,category_id=cat_id if cat_id else '')

        for prod in product_items:

            KeyScore.objects.get_or_create(num_iid=prod.num_iid,hotkey=hotkey_item)


    return HttpResponse(json.dumps({"code":0,"response_content":None}))



@csrf_exempt
def selectAndCancleKeys(request):

    new_keys  = request.POST.get('new_keys')
    old_keys  = request.POST.get('old_keys')
    num_iid   = request.POST.get('num_iid')

    new_keys  = json.loads(new_keys)
    old_keys  = json.loads(old_keys)

    if not num_iid  :
        return HttpResponse(json.dumps({"code":1,"response_error":"Num_iid can't be null."}))

    try:
        item_ins = ProductItem.objects.get(num_iid=num_iid)
    except ProductItem.DoesNotExist:
        return HttpResponse(json.dumps({"code":1,"response_error":"The num_iid doesnot be category."}))

    for key in old_keys:
        try:
            hotkey = Hotkey.objects.get(word=key,category_id=item_ins.category_id)
            ks_ins = KeyScore.objects.get(num_iid=num_iid,hotkey=hotkey)
            ks_ins.status = 0
            ks_ins.save()
        except Hotkey.DoesNotExist:
            continue
        except KeyScore.DoesNotExist:
            continue

    for key in new_keys:
        try:
            hotkey = Hotkey.objects.get(word=key,category_id=item_ins.category_id)
            ks_ins = KeyScore.objects.get(num_iid=num_iid,hotkey=hotkey)
            ks_ins.status = 1
            ks_ins.save()
        except Hotkey.DoesNotExist:
            continue
        except KeyScore.DoesNotExist:
            continue

    return HttpResponse(json.dumps({"code":0,"response_content":None}))



@csrf_exempt
def saveOrUpdateKeyScores(request):

    keyscores    = request.POST.get('keyscores')
    num_iid   = request.POST.get('num_iid')

    if not (num_iid and keyscores):
        return HttpResponse(json.dumps({"code":1,"response_error":"Num_iid and keyscores can't be null."}))

    keyscores   = json.loads(keyscores)

    try:
        item_ins = ProductItem.objects.get(num_iid=num_iid)
    except ProductItem.DoesNotExist:
        return HttpResponse(json.dumps({"code":1,"response_error":"The num_iid doesnot be category."}))

    for ks in keyscores:
        try:
            hotkey = Hotkey.objects.get(word=ks[0],category_id=item_ins.category_id)
        except Hotkey.DoesNotExist:
            continue
        try:
            ks_ins = KeyScore.objects.get(num_iid=num_iid,hotkey=hotkey)
            ks_ins.bid_price = ks[1]
            ks_ins.num_view = ks[2]
            ks_ins.num_click = ks[3]
            ks_ins.avg_cost = ks[4]*100
            ks_ins.score = ks[5]
            ks_ins.bid_rank = ks[6]
            ks_ins.modify = ks[7]
            ks_ins.status = 1
            ks_ins.save()
        except KeyScore.DoesNotExist:
            KeyScore.objects.create(num_iid=num_iid,hotkey=hotkey,
                num_view = ks[1],num_click = ks[2],avg_cost = ks[3]*100,score = ks[4],status=1)

    return HttpResponse(json.dumps({"code":0,"response_content":"success"}))



def getValuableHotKeys(request):
    type = request.GET.get("type", None)
    num_iid  = request.GET.get("num_iid", None)
    num_keys = int(request.GET.get("num", 20))

    if num_iid is None:
        return HttpResponse(json.dumps({"code": 1, "response_error": "no product id"}))

    sort_by = ''
    sort_ratio_by = ''
    if type == 'A':
        sort_by = 'num_people'
    elif type == 'B':
        sort_by = 'num_search'
    elif type == 'C':
        sort_by = 'num_click'
    elif type == 'D':
        sort_by = 'num_tmall_click'
    elif type == 'E':
        sort_by = 'num_cmall_click'
    elif type == 'F':
        sort_by = 'num_trade'
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
        return HttpResponse(json.dumps({"code":1,"response_error":'Search type is not in Supplied types!'}))

    hot_keyscores = KeyScore.objects.filter(num_iid=num_iid,status=0)
    if sort_by:
        hot_keyscores = hot_keyscores.order_by('-hotkey__'+sort_by).extra(select={'sort_value':sort_by})\
            .values('sort_value','num_iid','score','hotkey__word','hotkey_id')[:num_keys]
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
            hot_ks['sort_value']   = eval('hks.hotkey.'+sort_ratio_by)
            hot_ks['num_iid']      = hks.num_iid
            hot_ks['hotkey__word'] = hks.hotkey.word
            hot_ks['score']        = hks.score
            hot_ks['hotkey_id']    = hks.hotkey_id
            index = sortIndex('sort_value',hot_ks['sort_value'],hot_ks_dc)
            hot_ks_dc.insert(index,hot_ks)
        hot_keyscores = hot_ks_dc[:num_keys]

    return HttpResponse(json.dumps({"code":0,"response_content":hot_keyscores}))


def getClientCookie(request):

    rex_user_id = re.compile('unb=(?P<user_id>\w+);')
    rex_user_nick = re.compile('_nk_=(?P<user_nick>[\w%]+);')
    cookie = request.POST.get('subway_cookie')
    token = request.POST.get('token',None)
    campaignId = request.POST.get('campaignId',None)

    user_id_group = rex_user_id.search(cookie)
    user_nick_group = rex_user_nick.search(cookie)

    user_id = user_id_group.group('user_id')
    user_nick = user_nick_group.group('user_nick')

    if user_id and user_nick:
        request.session['subway_token'] = token
        request.session['campaignId']   = campaignId
        request.session['subway_user_id']   = user_id
        request.session['subway_user_nick'] = unquote(user_nick)
        request.session['subway_cookie']    = cookie

        return HttpResponse(json.dumps({"code":0,"response_content":"save cookie success!"}))
    else:
        return HttpResponse(json.dumps({"code":1,"response_error":"The userid or usernick is not in the cookie."}))



    


