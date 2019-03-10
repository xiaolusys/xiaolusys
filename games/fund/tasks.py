# coding: utf8
from __future__ import absolute_import, unicode_literals

import urllib2
import json

from shopmanager import celery_app as app

import logging
logger = logging.getLogger(__name__)



from .models import FundBuyerAccount, FundNotifyMsg

@app.task
def task_send_fund_profit_message():
    """ 发送基金收益消息给客户 """

    all_accounts = FundBuyerAccount.objects.filter(status=FundBuyerAccount.HOLDING)
    for ac in all_accounts:
        notify_data = ac.get_week_notify_data()

        FundNotifyMsg.objects.create(
            fund_buyer=ac,
            send_data=notify_data,
            send_type=FundNotifyMsg.WEEK_SEND,
        )
        


