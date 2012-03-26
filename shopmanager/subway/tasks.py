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



def saveTaociBycid(cat_id,keys):
    SRH_WRD=1; SRH_PPL=2; SRH_TMS=3; CLK_TMS=4; MAL_CLK=5; CML_CLK=6; NUM_TRD=8; PRICE=10;

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




def saveTaociLiftValueByCid(last_day_dt,cat_id,keys):

    n = keys[0][-1]
    for i in range(0,n):
        item = keys[0][i]
        TcKeyLift.objects.get_or_create(category_id=cat_id,word=item[1],lift_val=item[2],updated=last_day_dt)



def recurCrawTaoci(dt,base_dt,f_dt,t_dt,cat_id,taoci_cookie):
    try:
        #save category's taoci keys
        response,content = taoci_proxy(base_dt=base_dt,f_dt=f_dt,t_dt=t_dt,cat_id=cat_id,cookie=taoci_cookie)
        keys = json.loads(content)

        if isinstance(keys,dict) and keys.has_key('code'):
            logger.warn('get taoci fault,cat_id:%s,content%s'%(cat_id,content))


        saveTaociBycid(cat_id,keys)

        #save category's taoci lift_val
        last_day_dt = format_date(dt-datetime.timedelta(1,0,0))

        response,content = taoci_lift_proxy(base_dt=base_dt,f_dt=f_dt,t_dt=t_dt,cat_id=cat_id,cookie=taoci_cookie)
        keys = json.loads(content)

        if isinstance(keys,dict) and keys.has_key('code'):
            logger.warn('get taoci_lift fault,cat_id:%s,content%s'%(cat_id,content))

        saveTaociLiftValueByCid(last_day_dt,cat_id,keys)

        #wait 1 seconds ,then continue sub cat
        time.sleep(1)
    except Exception,exc:
            logger.error('saveCatsTaocibyCookieTask error:%s'%exc, exc_info=True)

    sub_cats = Category.objects.filter(parent_cid=cat_id)
    for cat in sub_cats:
        time.sleep(1)
        recurCrawTaoci(dt,base_dt,f_dt,t_dt,cat.cid,taoci_cookie)


@task()
def saveCatsTaocibyCookieTask(base_dt,f_dt,t_dt,cat_ids,taoci_cookie):
    dt = datetime.datetime.now()

    for cat_id in cat_ids:

        recurCrawTaoci(dt,base_dt,f_dt,t_dt,cat_id,taoci_cookie)

