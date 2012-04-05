import json
import datetime
import urllib
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from subway.models import Hotkey,TcKeyLift,ZtcItem,HotkeyStatic,KeyScore
from subway.apis import taoci_proxy,liangzi_proxy,taoci_lift_proxy
from subway.tasks import saveCatsTaocibyCookieTask,saveTaociAndLiftValue,updateHotkeyStatic
from auth.utils import format_date,parse_date
from subway.utils import DecimalEncoder
import logging

logger = logging.getLogger('subway.taoci')


@csrf_exempt
def updateTaociByCats(request):
    try:
        taoci_cookie = request.GET.get('taoci_cookie')
        f_dt   = request.GET.get('f_dt')
        t_dt   = request.GET.get('t_dt')
        cat_ids = request.GET.get('cat_ids')

        f_dt  = parse_date(f_dt)
        t_dt  = parse_date(t_dt)
        if not taoci_cookie or not cat_ids:
            return HttpResponse(json.dumps({"code":1,"response_error":"taoci_cookie or cat_ids needed!"}))

        cat_ids = cat_ids.split(',')
        tc_task = saveCatsTaocibyCookieTask.delay(f_dt,t_dt,cat_ids,taoci_cookie)

    except Exception,exc:
        logger.error('updateTaociByCats error:%s'%exc, exc_info=True)

    return HttpResponse(json.dumps({"code":0,"reponse_content":{"task_id":tc_task.task_id}}))




@csrf_exempt
def getOrUpdateTaociKey(request):

    taoci_cookie = request.GET.get('taoci_cookie')
    f_dt   = request.GET.get('f_dt')
    t_dt   = request.GET.get('t_dt')
    num_iid = request.GET.get('num_iid')
    id_map_key = request.GET.get('id_map_key')

    today = datetime.datetime.now()
    last_day = today - datetime.timedelta(1,0,0)
    last_day_dt = format_date(last_day)
    if not f_dt or not t_dt:
        f_dt = t_dt = last_day_dt

    try:
        cat_id = ZtcItem.objects.get(num_iid=num_iid).cat_id
    except ZtcItem.DoesNotExist:
        return HttpResponse(json.dumps({"code":1,"response_error":"Cat_id is not record!"}))

    f_dt  = parse_date(f_dt)
    t_dt  = parse_date(t_dt)

    del_dt  = t_dt-f_dt
    days =  del_dt.days if del_dt.days>0 else 1

    for i in xrange(0,days):
        time_delta = datetime.timedelta(i,0,0)
        last_few_days = format_date(t_dt - time_delta)
        ret_info = saveTaociAndLiftValue(last_few_days,cat_id,taoci_cookie)
        if ret_info:
            return HttpResponse(json.dumps(ret_info))
        updateHotkeyStatic.delay(cat_id)

    id_map_key = json.loads(id_map_key)
    hotkey_list = []
    for id,key in id_map_key:
        hk = []
        hk.append(id)
        try:
            hotkey = Hotkey.objects.get(category_id=cat_id,word=key,updated=last_day_dt)
        except Hotkey.DoesNotExist:
            hotkey=None
        try:
            key_lift = TcKeyLift.objects.get(category_id= cat_id,word=key,updated=last_day_dt)
        except TcKeyLift.DoesNotExist:
            key_lift = None

        hk.append(hotkey.num_people if hotkey else None)
        hk.append(hotkey.num_search if hotkey else None)
        hk.append(hotkey.num_click if hotkey else None)
        hk.append(hotkey.trade_click_ratio if hotkey else None)

        hk.append(key_lift.lift_val if key_lift else None)
        hotkey_list.append(hk)

    return HttpResponse(json.dumps(hotkey_list,indent=4),mimetype='application/json')




def getRecommendNewKey(request):

    num_iid = request.GET.get('num_iid')
    limit = int(request.GET.get('limit',50))

    dt = datetime.datetime.now()
    base_dt = format_date(dt - datetime.timedelta(1,0,0))

    try:
        cat_id = ZtcItem.objects.get(num_iid=num_iid).cat_id
    except ZtcItem.DoesNotExist:
        return HttpResponse(json.dumps({"code":1,"response_error":"Cat_id is not record!"}))

    rec_new_keys = Hotkey.getRecommendNewKey(base_dt,cat_id,limit)

    return HttpResponse(json.dumps(rec_new_keys,cls=DecimalEncoder),mimetype='application/json')




def getRecommendHotKey(request):

    num_iid = request.GET.get('num_iid')
    limit = int(request.GET.get('limit',800))

    today_dt = format_date(datetime.datetime.now()-datetime.timedelta(1,0,0))
    try:
        cat_id = ZtcItem.objects.get(num_iid=num_iid).cat_id
    except ZtcItem.DoesNotExist:
        return HttpResponse(json.dumps({"code":1,"response_error":"Cat_id is not record!"}))

    key_word_dict = KeyScore.objects.filter(num_iid=num_iid,updated=today_dt,status=1).values('word').distinct('word')

    key_word_set = set([key['word'] for key in key_word_dict])

    rec_hot_keys = HotkeyStatic.objects.filter(category_id=cat_id).order_by('-num_people').values_list\
        ('word','num_people','num_search', 'num_click','num_tmall_click','num_cmall_click','num_trade','ads_price_cent')[:limit]

    ret_hot_keys = []
    for hot_key in rec_hot_keys:
        temp_list = list(hot_key)

        try:
            key_word_set.remove(hot_key[0])
            temp_list.append(1)
        except Exception:
            temp_list.append(0)
        ret_hot_keys.append(temp_list)

    return HttpResponse(json.dumps(ret_hot_keys,cls=DecimalEncoder),mimetype='application/json')







