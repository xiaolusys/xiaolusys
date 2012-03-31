import re
import time
import json
import datetime
from celery.task import task
from celery.task.sets import subtask
from subway.apis import taoci_proxy,liangzi_proxy,taoci_lift_proxy
from shopback.categorys.models import Category
from subway.models import ZtcItem,LzKeyItem,TcKeyLift,Hotkey,HotkeyStatic
from auth.utils import format_datetime,format_date,parse_date
import logging

logger = logging.getLogger('taobao.taoci')


@task()
def updateHotkeyStatic(cat_id):
    try:
        dt = datetime.datetime.now()
        last_day_dt = format_date( dt - datetime.timedelta(1,0,0))
        seven_days_dt = format_date(dt - datetime.timedelta(14,0,0))

        HotkeyStatic.updateHotkeyStaticFromHotkey(cat_id,seven_days_dt,last_day_dt)
    except Exception,exc:
        logger.warn('updateHotkeyStatic error:%s'%exc,exc_info=True)



def saveTaociBycid(base_dt,cat_id,keys):
    SRH_WRD=1; SRH_PPL=2; SRH_TMS=3; CLK_TMS=4; MAL_CLK=5; CML_CLK=6; NUM_TRD=8; PRICE=10;

    n = keys[0][-1]
    for i in range(0,n):
        item = keys[0][i]

        Hotkey.objects.get_or_create(word=item[SRH_WRD],category_id=cat_id,num_people=item[SRH_PPL]
            ,num_search=item[SRH_TMS],num_click=item[CLK_TMS],num_tmall_click=item[MAL_CLK]
            ,num_cmall_click=item[CML_CLK],num_trade=item[NUM_TRD],ads_price_cent=item[PRICE]*100,updated=base_dt)




def saveTaociLiftValueByCid(base_dt,cat_id,keys):

    n = keys[0][-1]
    for i in range(0,n):
        item = keys[0][i]
        TcKeyLift.objects.get_or_create(category_id=cat_id,word=item[1],lift_val=item[2],updated=base_dt)




def saveTaociAndLiftValue(base_dt,cat_id,taoci_cookie):
    last_day_hotkey = Hotkey.objects.filter(category_id=cat_id,updated=base_dt)[0:1]

    if len(last_day_hotkey) == 0:
        #save category's taoci keys
        response,content = taoci_proxy(base_dt=base_dt,f_dt=base_dt,t_dt=base_dt,cat_id=cat_id,cookie=taoci_cookie)
        keys = json.loads(content)
        if isinstance(keys,dict) and keys.has_key('code'):
            logger.warn('get taoci fault,cat_id:%s,content%s'%(cat_id,content))
            return keys

        if keys and keys[0]:    #avoid keys value is ((),)
            saveTaociBycid(base_dt,cat_id,keys)

    last_day_keylift = TcKeyLift.objects.filter(category_id=cat_id,updated=base_dt)[0:1]

    if len(last_day_keylift) == 0:
        #save category's taoci lift_val
        response,content = taoci_lift_proxy(base_dt=base_dt,f_dt=base_dt,t_dt=base_dt,cat_id=cat_id,cookie=taoci_cookie)
        keys = json.loads(content)

        if isinstance(keys,dict) and keys.has_key('code'):
            logger.warn('get taoci_lift fault,cat_id:%s,content%s'%(cat_id,content))
            return keys

        if keys and keys[0]:    #avoid keys value is ((),)
            saveTaociLiftValueByCid(base_dt,cat_id,keys)




def recurCrawTaoci(f_dt,t_dt,cat_id,taoci_cookie):

    try:
        del_dt  = t_dt-f_dt
        days =  del_dt.days if del_dt.days>0 else 1
        for i in xrange(1,days+1):
            time_delta = datetime.timedelta(i,0,0)
            last_few_days = format_date(t_dt - time_delta)

            ret_val = saveTaociAndLiftValue(last_few_days,cat_id,taoci_cookie)
            if ret_val:
                return ret_val

    except Exception,exc:
        logger.error('saveCatsTaocibyCookieTask error:%s'%exc, exc_info=True)


    sub_cats = Category.objects.filter(parent_cid=cat_id)
    for cat in sub_cats:

        recurCrawTaoci(f_dt,t_dt,cat.cid,taoci_cookie)




@task()
def saveCatsTaocibyCookieTask(f_dt,t_dt,cat_ids,taoci_cookie):

    for cat_id in cat_ids:

        results = recurCrawTaoci(f_dt,t_dt,cat_id,taoci_cookie)

        if isinstance(results,dict) and results.has_key('code'):
            return results

        subtask(updateHotkeyStatic).delay(cat_id)


@task()
def deleteHotkeyAndLiftValueTask():

    dt = datetime.datetime.now()
    seven_day_ago = dt - datetime.timedelta(7,0,0)
    #delete out of last seven day's hotkey data
    Hotkey.objects.filter(updated<seven_day_ago).delete()
    #delete out of last seven day's tckeylift data
    TcKeyLift.objects.filter(updated<seven_day_ago).delete()

    logger.warn('excute deleteHotkeyAndLiftValueTask delete the data before %s'%seven_day_ago)


@task()
def saveZtcKeyScoreTask(id_map_key,num_iid):

    #"name",'0.26',1679,5,0.12,5,'102',1
    for id_key_list in id_map_key:
        pass




