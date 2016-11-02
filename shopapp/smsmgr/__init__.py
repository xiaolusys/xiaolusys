# -*- coding:utf8 -*-
from django.db.models import F
from .models import SMSPlatform, SMS_NOTIFY_ACTIVITY
from .service import SMS_CODE_MANAGER_TUPLE
from shopback import paramconfig as pcfg
import logging

logger = logging.getLogger(__name__)


def sendMessage(mobile, title, content, msgType=SMS_NOTIFY_ACTIVITY, SMS_PLATFORM_CODE=''):
    try:
        if SMS_PLATFORM_CODE:
            platform = SMSPlatform.objects.get(code=SMS_PLATFORM_CODE)
        else:
            platform = SMSPlatform.objects.get(is_default=True)
    except:
        return

    platform_code = platform.code
    params = {}
    params['content'] = content
    params['userid'] = platform.user_id
    params['account'] = platform.account
    params['password'] = platform.password
    params['mobile'] = mobile
    params['taskName'] = title
    params['mobilenumber'] = 1
    params['countnumber'] = 1
    params['telephonenumber'] = 0
    params['action'] = 'send'
    params['checkcontent'] = '0'

    sms_manager = dict(SMS_CODE_MANAGER_TUPLE).get(platform_code, None)
    if not sms_manager:
        raise Exception('未找到短信服务商接口实现')

    manager = sms_manager()
    success = False

    # 创建一条短信发送记录
    sms_record = manager.create_record(params['mobile'], params['taskName'], msgType, params['content'])
    # 发送短信接口
    try:
        success, task_id, succnums, response = manager.batch_send(**params)
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

    if success:
        SMSPlatform.objects.filter(code=platform_code).update(sendnums=F('sendnums') + int(succnums))

    return success


