# encoding=utf8
import logging
from django.db.models import F
from django.conf import settings
from shopapp.smsmgr.models import (
    SMSPlatform,
    SMSActivity,
    choice_sms_notify_type,
    SMS_NOTIFY_MAMA_ORDERCARRY,
    SMS_NOTIFY_APP_UPDATE,
    SMS_NOTIFY_MAMA_SUBSCRIBE_WEIXIN,
    SMS_NOTIFY_GOODS_LACK
)
from shopapp.smsmgr.service import SMS_CODE_MANAGER_TUPLE
from shopapp.smsmgr.tasks import call_send_a_sms

logger = logging.getLogger('service')


class SMSPush(object):

    def __init__(self):
        if not settings.SMS_PUSH_SWITCH:
            return

        self.platform = SMSPlatform.objects.filter(is_default=True) \
                                           .order_by('-id').first()
        self.manager = dict(SMS_CODE_MANAGER_TUPLE).get(self.platform.code, None)()

    def push(self, to_mobile, content, sms_notify_type):
        if not settings.SMS_PUSH_SWITCH:
            return

        task_name = dict(choice_sms_notify_type()).get(sms_notify_type, None)
        params = {
            'content': content,
            'userid': self.platform.user_id,
            'account': self.platform.account,
            'password': self.platform.password,
            'mobile': to_mobile,
            'taskName': task_name,
            'mobilenumber': 1,
            'countnumber': 1,
            'telephonenumber': 0,
            'action': 'send',
            'checkcontent': '0'
        }
        succnums, success = call_send_a_sms(self.manager, params, sms_notify_type)

        logger.info({
            'action': 'push.smspush',
            'to_mobile': to_mobile,
            'task_name': task_name,
            'content': content,
            'success': success,
        })

        if success:
            SMSPlatform.objects.filter(code=self.platform.code) \
                               .update(sendnums=F('sendnums') + int(succnums))

    def push_mama_ordercarry(self, customer, money):
        """
        有新的订单收益推送给小鹿妈妈
        """
        to_mobile = customer.mobile
        sms_notify_type = SMS_NOTIFY_MAMA_ORDERCARRY

        sms_tpl = SMSActivity.objects.filter(sms_type=sms_notify_type, status=True).first()
        if sms_tpl:
            content = sms_tpl.text_tmpl.format(money)
            self.push(to_mobile, content, sms_notify_type)

    def push_mama_update_app(self, customer):
        to_mobile = customer.mobile
        sms_notify_type = SMS_NOTIFY_APP_UPDATE

        sms_tpl = SMSActivity.objects.filter(sms_type=sms_notify_type, status=True).first()
        if sms_tpl:
            content = sms_tpl.text_tmpl
            self.push(to_mobile, content, sms_notify_type)

    def push_mama_subscribe_weixin(self, customer):
        """
        引导一元妈妈关注小鹿美美
        """
        to_mobile = customer.mobile
        sms_notify_type = SMS_NOTIFY_MAMA_SUBSCRIBE_WEIXIN

        sms_tpl = SMSActivity.objects.filter(sms_type=sms_notify_type, status=True).first()
        if sms_tpl:
            content = sms_tpl.text_tmpl
            self.push(to_mobile, content, sms_notify_type)
