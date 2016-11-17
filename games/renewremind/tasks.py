# coding=utf-8
from __future__ import absolute_import, unicode_literals

import datetime
import logging
from shopmanager import celery_app as app
from django.db.models import F

from games.renewremind import constants
from games.renewremind.models import RenewRemind
from shopback import paramconfig as pcfg
from shopapp.smsmgr.models import SMSPlatform, SMS_NOTIFY_TOCITY
from shopapp.smsmgr.service import SMS_CODE_MANAGER_TUPLE

logger = logging.getLogger(__name__)


def send_message(mobile, message, taskName):
    try:
        platform = SMSPlatform.objects.get(is_default=True)
    except:
        logger.error(u'默认短信供应商出错,请及时处理!!!')
        return
    try:
        params = {'content': message,
                  'userid': platform.user_id,
                  'account': platform.account,
                  'password': platform.password,
                  'mobile': mobile,
                  'taskName': taskName,
                  'mobilenumber': 1,
                  'countnumber': 1,
                  'telephonenumber': 0,
                  'action': 'send',
                  'checkcontent': '0'}
        sms_manager = dict(SMS_CODE_MANAGER_TUPLE).get(platform.code, None)
        manager = sms_manager()
        sms_record = manager.create_record(params['mobile'],
                                           params['taskName'],
                                           SMS_NOTIFY_TOCITY,
                                           params['content'])
        # 发送短信接口
        try:
            success, task_id, succnums, response = manager.batch_send(**params)
            if success:  # 如果成功发送则更新发送的短信条数
                SMSPlatform.objects.filter(code=platform.code).update(sendnums=F('sendnums') + int(succnums))
        except Exception, exc:
            sms_record.status = pcfg.SMS_ERROR
            sms_record.memo = exc.message
            logger.error(exc.message, exc_info=True)
        else:
            sms_record.task_id = task_id
            sms_record.succnums = succnums
            sms_record.retmsg = response
            sms_record.status = success and pcfg.SMS_COMMIT or pcfg.SMS_ERROR
        sms_record.save()
    except Exception, exc:
        logger.error(exc.message or '%s发送出错' % taskName, exc_info=True)


@app.task()
def trace_renew_remind_send_msm():
    """ 追踪续费服务提醒记录处理 """
    reminds = RenewRemind.objects.filter(is_trace=True)  # 在追踪状态的续费提醒记录
    for remind in reminds:
        now = datetime.datetime.now()
        now_ahead = now + datetime.timedelta(days=constants.REMIND_SEND_MESSAGE_DAYS)
        # 提醒时间如果在未来时间的一个月（暂定）以内则发送短信提醒管理员　否则跳过
        if remind.expire_time <= now_ahead:
            # 项目名称
            msg = '系统后台服务' + remind.project_name + '将到期,时间:' + remind.expire_time.strftime('%Y-%m-%d') + '请及时续费!'
            send_message(remind.principal_phone, msg, taskName='续费服务提醒')
            send_message(remind.principal2_phone, msg, taskName='续费服务提醒')
            send_message(remind.principal3_phone, msg, taskName='续费服务提醒')
