import json
import time
import datetime
import urllib
from django.http import HttpResponse
from subway.models import LzKeyItem
from subway.apis import taoci_proxy,liangzi_proxy,taoci_lift_proxy
from subway.tasks import saveCatsTaocibyCookieTask
from auth.utils import format_time,parse_datetime,format_datetime,format_date,parse_date
import logging

logger = logging.getLogger('subway.liangzi')


def saveLzKeyItems(dt,owner,limit,lzsession):
    lz_keys = LzKeyItem.objects.filter(owner=owner,updated=dt)[0:1]
    if len(lz_keys)==0:
        try:
            response,content = liangzi_proxy(limit=limit,f_dt=dt,t_dt=dt,session=lzsession)
            lz_data_list = json.loads(content)
            lz_data_list = lz_data_list.get('list',[])

            if not lz_data_list:
                logger.error('get seller liangzi data fault,return content:%s'%content)

            for lz_data in lz_data_list:

                lz_key,create = LzKeyItem.objects.get_or_create\
                        (owner=owner,update=dt,auction_id=lz_data['auction_id'],originalword=lz_data['originalword'])
                if create:
                    for k,v in lz_data.iteritems():
                        hasattr(lz_key,k) and setattr(lz_key,k,v)
                    lz_key.effect_rank = lz_data['effect_rank'] if lz_data['effect_rank'] else '0'
                    lz_key.efficiency  = lz_data['efficiency'] if lz_data['efficiency'] else '0'
                    lz_key.save()

        except Exception,exc:
            logger.error(' saveLzKeyItems error:%s'%exc, exc_info=True)




def updateLzKeysItems(request):

    lzsession = request.GET.get('lzsession')
    lz_f_dt = request.GET.get('lz_f_dt')
    lz_t_dt = request.GET.get('lz_t_dt')
    owner     = request.GET.get('owner')
    limit     = request.GET.get('limit',100)

    dt = datetime.datetime.now()
    if not (lz_f_dt and lz_t_dt):
        ten_day_ago   = dt - datetime.timedelta(10,0,0)
        three_day_ago = dt - datetime.timedelta(3,0,0)
        lz_f_dt = ten_day_ago
        lz_t_dt = three_day_ago
    else:
        lz_f_dt = parse_date(lz_f_dt)
        lz_t_dt = parse_date(lz_t_dt)
        det_dt = dt - lz_t_dt
        if det_dt.days<3:
            lz_t_dt = dt - datetime.timedelta(3,0,0)

    del_dt  = lz_t_dt-lz_f_dt
    days =  del_dt.days if del_dt.days>0 else 1
    for i in xrange(0,days):
        time_delta = datetime.timedelta(i,0,0)
        last_few_days = format_date(lz_t_dt - time_delta)
        saveLzKeyItems(last_few_days,owner,limit,lzsession)

    return HttpResponse(json.dumps({"code":0}))




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

    dt = datetime.datetime.now()
    if not (lz_f_dt and lz_t_dt):
        ten_day_ago   = dt - datetime.timedelta(10,0,0)
        three_day_ago = dt - datetime.timedelta(3,0,0)
        lz_f_dt = ten_day_ago
        lz_t_dt = three_day_ago
    else:
        lz_f_dt = parse_date(lz_f_dt)
        lz_t_dt = parse_date(lz_t_dt)
        det_dt = dt - lz_t_dt
        if det_dt.days<3:
            lz_t_dt = dt - datetime.timedelta(3,0,0)

    del_dt  = lz_t_dt-lz_f_dt
    days =  del_dt.days if del_dt.days>0 else 1
    for i in xrange(0,days):
        time_delta = datetime.timedelta(i,0,0)
        last_few_days = format_date(lz_t_dt - time_delta)
        saveLzKeyItems(last_few_days,owner,limit,lzsession)

    keys = [ key.encode('utf8') for key in keys]
    key_str   = ','.join(["'"+key+"'" for key in keys])

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