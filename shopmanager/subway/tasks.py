import re
import time
import json
import datetime
from celery.task import task
from celery.task.sets import subtask
from subway.apis import taoci_proxy,liangzi_proxy,taoci_lift_proxy
from shopback.categorys.models import Category
from subway.models import ZtcItem,LzKeyItem,TcKeyLift,Hotkey
from auth.utils import format_datetime,format_date
import logging

logger = logging.getLogger('taobao.taoci')



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




def recurCrawTaoci(last_day_dt,cat_id,taoci_cookie):

    try:
        ht_key  = Hotkey.objects.filter(category_id=cat_id)\
            .extra(select={'lastest_update':'MAX(updated)'}).values('lastest_update')

        lastest_update = ht_key[0]['lastest_update']

        if not lastest_update or lastest_update<last_day_dt:
            today = datetime.datetime.now()
            for i in xrange(1,7):
                time_delta = datetime.timedelta(i,0,0)
                last_few_days = format_date(today - time_delta)

                if not lastest_update or lastest_update<last_few_days:
                    ret_val = saveTaociAndLiftValue(last_few_days,cat_id,taoci_cookie)
                    if ret_val:
                        return ret_val

    except Exception,exc:
            logger.error('saveCatsTaocibyCookieTask error:%s'%exc, exc_info=True)

    sub_cats = Category.objects.filter(parent_cid=cat_id)
    for cat in sub_cats:

        recurCrawTaoci(last_day_dt,cat.cid,taoci_cookie)




@task()
def saveCatsTaocibyCookieTask(cat_ids,taoci_cookie):
    dt = datetime.datetime.now()
    last_day_dt = format_date(dt-datetime.timedelta(1,0,0))
    for cat_id in cat_ids:

        results = recurCrawTaoci(last_day_dt,cat_id,taoci_cookie)

        if isinstance(results,dict) and results.has_key('code'):
            return results

