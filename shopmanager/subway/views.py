import re
import json
import time
import decimal
import urllib
import datetime
from django.http import HttpResponse
from django.db.models import Max,Sum
from django.views.decorators.csrf import csrf_exempt
from subway.models import Hotkey, KeyScore, ZtcItem,LzKeyItem,TcKeyLift
from autolist.models import ProductItem
from auth.utils import unquote
from subway.apis import taoci_proxy,liangzi_proxy,taoci_lift_proxy
from auth.utils import format_time,parse_datetime,format_datetime,format_date
from subway.utils import access_control_allow_origin
import logging

logger = logging.getLogger('subway.hotkey')


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




def saveKeyScores(request):

    key_scores  = request.GET.get('key_scores')
    num_iid    = request.GET.get('num_iid')
    campaign_id   = request.GET.get('campaign_id')

    key_scores   = json.loads(key_scores)
    dt = datetime.datetime.now()
    last_day_dt  = format_date(dt-datetime.timedelta(1,0,0))

    for ks in key_scores:

        ks_ins,state = KeyScore.objects.get_or_create\
                (word=ks[0],num_iid=num_iid,campaign_id=campaign_id,updated=last_day_dt)
        if state:
            ks_ins.bid_price = ks[1]
            ks_ins.num_view  = ks[2]
            ks_ins.num_click = ks[3]
            ks_ins.avg_cost  = ks[4]
            ks_ins.score     = ks[5]
            ks_ins.bid_rank  = ks[6]
            ks_ins.updated   = last_day_dt
            ks_ins.status    = 1
            ks_ins.save()

    return HttpResponse(json.dumps({"code":0,"response_content":"success"}))





@access_control_allow_origin
def getCatHotKeys(request):

    num_iid = request.GET.get('num_iid')
    id_map_key = request.GET.get('id_map_key')
    lz_f_dt = request.GET.get('lz_f_dt')
    lz_t_dt = request.GET.get('lz_t_dt')

    id_map_key = json.loads(id_map_key)

    #key_map_id = dict([(key[1],key[0]) for key in id_map_key])
    #keys = key_map_id.keys()

    if not (lz_f_dt and lz_t_dt):
        ten_day_ago   = datetime.datetime.now() - datetime.timedelta(10,0,0)
        three_day_ago = datetime.datetime.now() - datetime.timedelta(3,0,0)
        lz_f_dt = format_date(ten_day_ago)
        lz_t_dt = format_date(three_day_ago)

    try:
        cat_id = ZtcItem.objects.get(num_iid=num_iid).cat_id
    except ZtcItem.DoesNotExist:
        return HttpResponse(json.dumps({"code":1,"response_error":"Cat_id is not record!"}))

    last_day_dt = format_date(datetime.datetime.now()-datetime.timedelta(1,0,0))

    hotkey_list = []
    for id,key in id_map_key:
        hk = []
        hk.append(id)
        try:
            hotkey = Hotkey.objects.get(category_id=cat_id,word=key,updated=last_day_dt)
        except Hotkey.DoesNotExist:
            hotkey = None

        lz_key = LzKeyItem.objects.filter(auction_id=num_iid,originalword=key)\
            .filter(updated__gte=lz_f_dt,updated__lte=lz_t_dt)\
            .aggregate(collnums=Sum('coll_num'),finclicks=Sum('finclick'),finprices=Sum('finprice')
                       ,alipay_amts=Sum('alipay_amt'),alipay_nums=Sum('alipay_num'))
        try:
            key_lift = TcKeyLift.objects.get(category_id= cat_id,word=key,updated=last_day_dt)
        except TcKeyLift.DoesNotExist:
            key_lift = None

        hk.append(key)
        hk.append(hotkey.num_people if hotkey else None)
        hk.append(hotkey.num_search if hotkey else None)
        hk.append(hotkey.num_click if hotkey else None)
        hk.append(hotkey.trade_click_ratio if hotkey else None)
        hk.append(lz_key['finprices'])
        hk.append(lz_key['finclicks'])
        hk.append(lz_key['alipay_amts'])
        hk.append(lz_key['alipay_nums'])
        hk.append(lz_key['collnums'])
        hk.append(key_lift.lift_val if key_lift else None)

        hotkey_list.append(hk)

    return HttpResponse(json.dumps(hotkey_list,indent=4),mimetype='application/json')



@csrf_exempt
def saveZtcItem(request):

    owner = request.GET.get('owner', None)
    num_iid = request.GET.get('num_iid', None)
    cat_id = request.GET.get('cat_id', None)
    cat_name = request.GET.get('cat_name', None)

    if (owner and num_iid and cat_id and cat_name):
        ZtcItem.objects.create(owner=owner,num_iid=num_iid,cat_id=cat_id,cat_name=cat_name)
        return HttpResponse(json.dumps({"code":0}))

    return HttpResponse(json.dumps({"code":1}))





        

    


