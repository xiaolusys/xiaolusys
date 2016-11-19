# coding=utf-8
from __future__ import absolute_import, unicode_literals

import datetime
from shopmanager import celery_app as app
from django.db.models import F

from games.renewremind import constants
from games.renewremind.models import RenewRemind
from shopapp.smsmgr.apis import send_sms_message, SMS_TYPE

import logging
logger = logging.getLogger(__name__)



@app.task()
def trace_renew_remind_send_msm():
    """ 追踪续费服务提醒记录处理 """
    reminds = RenewRemind.objects.filter(is_trace=True)  # 在追踪状态的续费提醒记录
    for remind in reminds:
        now = datetime.datetime.now()
        now_ahead = now + datetime.timedelta(days=constants.REMIND_SEND_MESSAGE_DAYS)
        # 提醒时间如果在未来时间的一个月（暂定）以内则发送短信提醒管理员　否则跳过
        if remind.expire_time > now_ahead:
            continue

        params = {
            'sms_project_name': remind.project_name,
            'sms_expire_time': remind.expire_time.strftime('%Y-%m-%d'),
        }

        send_sms_message(
            [remind.principal_phone, remind.principal2_phone, remind.principal3_phone],
            msg_type=SMS_TYPE.SMS_NOTIFY_MAMARENEW,
            **params
        )




