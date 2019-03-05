# coding: utf8
from __future__ import absolute_import, unicode_literals

import urllib2
import json

from shopmanager import celery_app as app

import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from shopapp.weixin.apis.wxpubsdk import WeiXinAPI

from .models import FundBuyerAccount, FundNotifyMsg

@app.task
def task_send_fund_profit_message():
    """ 发送基金收益消息给客户 """

    wx_api = WeiXinAPI()
    wx_api.setAccountId(appKey=settings.WX_HGT_APPID)

    all_accounts = FundBuyerAccount.objects.filter(status=FundBuyerAccount.HOLDING)
    for ac in all_accounts:
        notify_data = ac.get_week_notify_data()

        notify_obj  = FundNotifyMsg.objects.create(
            fund_buyer=ac,
            send_data=notify_data,
            send_type=FundNotifyMsg.WEEK_SEND,
        )
        
        wx_api.send_mass_message(
            {
                "touser": [
                    ac.openid, #接口要求必须两个openid, 所以重复参数
                    ac.openid
                ],
                "msgtype": "text",
                "text": {"content": notify_obj.get_notify_message()}
            })

        notify_obj.confirm_send()

