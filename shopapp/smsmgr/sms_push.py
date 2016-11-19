# encoding=utf8
import logging

from shopapp.smsmgr.apis import send_sms_message, SMS_TYPE

logger = logging.getLogger('service')


class SMSPush(object):

    def __init__(self):
        pass

    def push_mama_ordercarry(self, customer, money):
        """
        有新的订单收益推送给小鹿妈妈
        """
        to_mobile = customer.mobile
        params = {
            'sms_commission': money
        }
        send_sms_message(to_mobile, msg_type=SMS_TYPE.SMS_NOTIFY_MAMA_ORDERCARRY, **params)

    def push_mama_update_app(self, customer):
        """
        app更新通知小鹿妈妈
        """
        to_mobile = customer.mobile
        params = {
        }
        send_sms_message(to_mobile, msg_type=SMS_TYPE.SMS_NOTIFY_APP_UPDATE, **params)


    def push_mama_subscribe_weixin(self, customer):
        """
        引导一元妈妈关注小鹿美美
        """
        to_mobile = customer.mobile
        params = {
        }
        send_sms_message(to_mobile, msg_type=SMS_TYPE.SMS_NOTIFY_MAMA_SUBSCRIBE_WEIXIN, **params)
