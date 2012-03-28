import json
import time
import datetime
import urllib
from django.http import HttpResponse
from subway.models import LzKeyItem
from subway.apis import taoci_proxy,liangzi_proxy,taoci_lift_proxy
from subway.tasks import saveCatsTaocibyCookieTask
from auth.utils import format_time,parse_datetime,format_datetime,format_date
import logging

logger = logging.getLogger('subway.liangzi')


def saveLzKeyItems(dt,owner,limit,lzsession):
    try:
        response,content = liangzi_proxy(limit=limit,f_dt=dt,t_dt=dt,session=lzsession)
        lz_data_list = json.loads(content)
        lz_data_list = lz_data_list.get('list',None)

        if not lz_data_list:
            logger.error('get seller liangzi data fault,return content:%s'%content)

        lz_key = LzKeyItem()
        lz_key.updated = dt
        lz_key.owner  = owner

        for lz_data in lz_data_list:

            lz_key.id = None
            for k,v in lz_data.iteritems():
                hasattr(lz_key,k) and setattr(lz_key,k,v)
            lz_key.effect_rank = lz_data['effect_rank'] if lz_data['effect_rank'] else '0'
            lz_key.efficiency  = lz_data['efficiency'] if lz_data['efficiency'] else '0'
            lz_key.save()

    except Exception,exc:
        logger.error(' saveLzKeyItems error:%s'%exc, exc_info=True)




def updateLzKeysItems(request):

    lzsession = request.GET.get('lzsession')
    owner     = request.GET.get('owner')
    limit     = request.GET.get('limit',100)

    lzkey  = LzKeyItem.objects.filter(owner=owner).\
        extra(select={'lastest_update':'MAX(updated)'}).values('lastest_update')

    lastest_update = lzkey[0]['lastest_update']
    is_modify = False
    today = datetime.datetime.now()
    last_four_days = format_date(today - datetime.timedelta(4,0,0))

    if not lastest_update or lastest_update<last_four_days:
        for i in xrange(3,10):
            time_delta = datetime.timedelta(i,0,0)
            last_few_days = format_date(today - time_delta)
            if not lastest_update or lastest_update<last_few_days:
                saveLzKeyItems(last_few_days,owner,limit,lzsession)
                is_modify = True
                time.sleep(1)

    elif lastest_update == last_four_days:

        dt = format_date(today - datetime.timedelta(3,0,0))
        saveLzKeyItems(dt,owner,limit,lzsession)
        is_modify = True

    return HttpResponse(json.dumps({"code":0,"modified":1 if is_modify else 0}))




def getOrUpdateLiangZiKey(request):

    num_iid = request.GET.get('num_iid')
    id_map_key = request.GET.get('id_map_key')
    lz_f_dt = request.GET.get('lz_f_dt')
    lz_t_dt = request.GET.get('lz_t_dt')
    lzsession = request.GET.get('lzsession')
    owner     = request.GET.get('owner')
    limit     = request.GET.get('limit',100)

    id_map_key = json.loads(id_map_key)
    key_map_id = dict([(key[1],key[0]) for key in id_map_key])
    keys = key_map_id.keys()

    if not (lz_f_dt and lz_t_dt):
        ten_day_ago   = datetime.datetime.now() - datetime.timedelta(10,0,0)
        three_day_ago = datetime.datetime.now() - datetime.timedelta(3,0,0)
        lz_f_dt = format_date(ten_day_ago)
        lz_t_dt = format_date(three_day_ago)

    lz_key_items = LzKeyItem.objects.filter(updated__gte=lz_t_dt,updated__lte=lz_t_dt)[0:1]

    if len(lz_key_items) == 0:

        lzkey  = LzKeyItem.objects.filter(owner=owner).\
            extra(select={'lastest_update':'MAX(updated)'}).values('lastest_update')

        lastest_update = lzkey[0]['lastest_update']

        today = datetime.datetime.now()
        last_four_days = format_date(today - datetime.timedelta(4,0,0))

        if not lastest_update or lastest_update<last_four_days:
            for i in xrange(3,10):
                time_delta = datetime.timedelta(i,0,0)
                last_few_days = format_date(today - time_delta)
                if not lastest_update or lastest_update<last_few_days:
                    saveLzKeyItems(last_few_days,owner,limit,lzsession)
                    time.sleep(1)

        elif lastest_update == last_four_days:
            dt = format_date(today - datetime.timedelta(3,0,0))
            saveLzKeyItems(dt,owner,limit,lzsession)

    keys = [ key.encode('utf8') for key in keys]
    key_str   = ','.join(keys)
    lz_key_tuple = LzKeyItem.getGroupAttrsByIdAndWord(num_iid,key_str,lz_f_dt,lz_t_dt)

    lz_key_list  = []
    for lz_key_t in lz_key_tuple:
        lz_key_l = []
        lz_key_l.append(key_map_id.get(lz_key_t[0],None))
        lz_key_l.append(lz_key_t[0])
        lz_key_l.append(int(lz_key_t[1]))
        lz_key_l.append(int(lz_key_t[2]))
        lz_key_l.append(int(lz_key_t[3]))
        lz_key_l.append(int(lz_key_t[4]))
        lz_key_l.append(int(lz_key_t[5]))
        lz_key_list.append(lz_key_l)

    return HttpResponse(json.dumps(lz_key_list),mimetype='application/json')