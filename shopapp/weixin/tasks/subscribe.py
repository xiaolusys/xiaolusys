# coding: utf8
import datetime
from celery.task import task

from shopapp.weixin.weixin_apis import WeiXinAPI
from shopapp.weixin.models import WeixinFans, WeixinUnionID

import logging
logger = logging.getLogger(__name__)

@task(max_retries=3, default_retry_delay=5)
def task_subscribe_or_unsubscribe_update_userinfo(openid, wx_pubid, event, eventKey):
    try:
        wx_api = WeiXinAPI()
        wx_api.setAccountId(wxpubId=wx_pubid)
        app_key = wx_api.getAccount().app_id

        if event == 'subscribe':
            user_info = wx_api.getCustomerInfo(openid)
            unionid   = user_info['unionid']
            fans = WeixinFans.objects.filter(app_key=app_key, openid=openid).first()
            if not fans:
                fans = WeixinFans()
            fans.openid = openid
            fans.app_key = app_key
            fans.unionid = unionid
            fans.subscribe = True
            fans.subscribe_time = datetime.datetime.now()
            if eventKey:
                fans.set_qrscene(eventKey.lower().replace('qrscene_',''))
            fans.save()

            WeixinUnionID.objects.get_or_create(
                openid=openid,
                app_key=app_key,
                unionid=unionid,
            )
        elif event == 'unsubscribe':
            fans = WeixinFans.objects.filter(app_key=app_key, openid=openid).first()
            if fans:
                fans.subscribe = False
                fans.unsubscribe_time = datetime.datetime.now()
                fans.save()
    except Exception, exc:
        raise task_subscribe_or_unsubscribe_update_userinfo.retry(exc=exc)