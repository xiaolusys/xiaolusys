# coding: utf8
from __future__ import absolute_import, unicode_literals
__all__ = ['send_sms_message', 'SMS_TYPE']

from .. import models as SMS_TYPE #just call the SMS_NOTIFY_[name] var
from ..services import  get_sms_manager_by_code

def send_sms_message(mobiles, msg_type=None, SMS_PLATFORM_CODE=None, **kwargs):
    """
        短信发送接口
        所有要转入模板的参数都应以 sms_[name] 格式:
          sms_code: 12345
    """
    manager_class = get_sms_manager_by_code(SMS_PLATFORM_CODE)
    if not manager_class:
        return False

    sms_manager = manager_class()
    success = sms_manager.on_send(mobiles, msg_type, **kwargs)
    return success

