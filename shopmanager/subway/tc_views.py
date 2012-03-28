import json
import datetime
import decimal
import urllib
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from subway.models import Hotkey, TcKeyLift,ZtcItem
from subway.apis import taoci_proxy,liangzi_proxy,taoci_lift_proxy
from subway.tasks import saveCatsTaocibyCookieTask
from auth.utils import format_date
import logging

logger = logging.getLogger('subway.taoci')


@csrf_exempt
def updateTaociByCats(request):
    try:
        taoci_cookie = request.POST.get('taoci_cookie')
        base_dt = request.POST.get('base_dt')
        f_dt   = request.POST.get('f_dt')
        t_dt   = request.POST.get('t_dt')
        cat_ids = request.POST.get('cat_ids')

        if not taoci_cookie or not cat_ids:
            return HttpResponse(json.dumps({"code":1,"response_error":"taoci_cookie or cat_ids needed!"}))

        if not base_dt or not f_dt or not t_dt:
            dt = datetime.datetime.now()
            last_day = dt - datetime.timedelta(1,0,0)
            base_dt = f_dt = t_dt = format_date(last_day)

        cat_ids = cat_ids.split(',')
        taoci_cookie = urllib.unquote(taoci_cookie)

        tc_task = saveCatsTaocibyCookieTask.delay(base_dt,f_dt,t_dt,cat_ids,taoci_cookie)

    except Exception,exc:
        logger.error('updateTaociByCats error:%s'%exc, exc_info=True)

    return HttpResponse(json.dumps({"code":0,"reponse_content":{"task_id":tc_task.task_id}}))




@csrf_exempt
def getOrUpdateTaociKey(request):

    taoci_cookie = request.GET.get('taoci_cookie')
    base_dt = request.GET.get('base_dt')
    f_dt   = request.GET.get('f_dt')
    t_dt   = request.GET.get('t_dt')
    num_iid = request.GET.get('num_iid')
    id_map_key = request.GET.get('id_map_key')

    if not base_dt or not f_dt or not t_dt:
        dt = datetime.datetime.now()
        last_day = dt - datetime.timedelta(1,0,0)
        base_dt = f_dt = t_dt = format_date(last_day)

    cat_id = ZtcItem.objects.get(num_iid=num_iid).cat_id
    taoci_list = Hotkey.objects.filter(category_id=cat_id,updated__gte=f_dt,updated__lte=t_dt)
    if taoci_list.count()==0:
        if not taoci_cookie or not cat_id:
            return HttpResponse(json.dumps({"code":1,"response_error":"Taoci_cookie or cat_id needed!"}))

        cat_ids = [cat_id]
        taoci_cookie = urllib.unquote(taoci_cookie)

        tc_task = saveCatsTaocibyCookieTask.delay(base_dt,f_dt,t_dt,cat_ids,taoci_cookie)
        return HttpResponse(json.dumps({"code":0,"response_content":{"task_id":tc_task.task_id}}))

    id_map_key = json.loads(id_map_key)
    hotkey_list = []
    for id,key in id_map_key:
        hk = []
        hk.append(id)
        try:
            hotkey = Hotkey.objects.get(category_id=cat_id,word=key,updated=base_dt)
        except Hotkey.DoesNotExist:
            hotkey=None
        try:
            key_lift = TcKeyLift.objects.get(category_id= cat_id,word=key,updated=base_dt)
        except TcKeyLift.DoesNotExist:
            key_lift = None

        hk.append(hotkey.num_people if hotkey else None)
        hk.append(hotkey.num_search if hotkey else None)
        hk.append(hotkey.num_click if hotkey else None)
        hk.append(hotkey.trade_click_ratio if hotkey else None)

        hk.append(key_lift.lift_val if key_lift else None)
        hotkey_list.append(hk)

    return HttpResponse(json.dumps(hotkey_list,indent=4),mimetype='application/json')




def getRecommendNewAndHotKey(request):

    cat_id = request.GET.get('cat_id')
    base_dt = request.GET.get('base_dt')
    f_dt   = request.GET.get('f_dt')
    t_dt   = request.GET.get('t_dt')
    limit = int(request.GET.get('limit',50))

    if not base_dt or not f_dt or not t_dt:
        dt = datetime.datetime.now()
        last_day_dt = format_date(dt - datetime.timedelta(1,0,0))
        base_dt = f_dt = t_dt = last_day_dt

    rec_hot_keys = Hotkey.objects.extra(
        select={"search_ratio":"ROUND(num_trade/num_search,4)"},
        where=['id in (select id from subway_hotkey where updated=%s and category_id=%s and num_people>1500 )'],
        params=[base_dt,cat_id]).order_by('-search_ratio')\
        .values_list('word','num_people','num_search','num_click','num_trade','ads_price_cent','search_ratio')[:limit]

    rec_hot_keys = [key for key in rec_hot_keys]
    rec_new_keys = Hotkey.getRecommendNewKey(base_dt,cat_id,limit)

    results = {"rec_hot_keys":rec_hot_keys,"rec_new_keys":rec_new_keys}

    class DecimalEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj,decimal.Decimal):
                return str(obj)
            return json.JSONEncoder.default(self, obj)

    return HttpResponse(json.dumps(results,cls=DecimalEncoder),mimetype='application/json')