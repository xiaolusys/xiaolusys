# coding=utf-8
"""
代理相关推送
"""
import logging
from flashsale.push.mipush import mipush_of_ios, mipush_of_android
from flashsale.push import constants as push_constants
from flashsale.protocol import get_target_url
from flashsale.protocol import constants as protocal_constants
from flashsale.push.models_message import PushMsgTpl


logger = logging.getLogger('service')


def push_msg_to_mama(message):
    """ 发送app推送(一个一个推送) """

    def _wrapper(mama):
        customer = mama.get_mama_customer()
        if not customer:
            return
        customer_id = customer.id
        target_url = get_target_url(protocal_constants.TARGET_TYPE_HOME_TAB_1)
        msg = None
        if message:
            msg = message
        else:
            mstpls = PushMsgTpl.objects.filter(id=6, is_valid=True)
            if mstpls.exists():
                mstpl = mstpls[0]
                msg = mstpl.get_emoji_content()
        if msg is not None:
            mipush_of_android.push_to_account(customer_id,
                                              {'target_url': target_url},
                                              description=msg)
            mipush_of_ios.push_to_account(customer_id,
                                          {'target_url': target_url},
                                          description=msg)
            logger.info({
                'action': 'push.mipush.push_msg_to_mama',
                'customer': customer_id,
                'msg': msg,
                'target_url': target_url,
            })

    return _wrapper


def push_msg_to_topic_mama(message):
    """ 发送九张图更新app推送(批量) """
    target_url = get_target_url(protocal_constants.TARGET_TYPE_HOME_TAB_1)
    if message:
        mipush_of_android.push_to_topic(push_constants.TOPIC_XLMM_A,
                                        {'target_url': target_url},
                                        description=message)
        mipush_of_ios.push_to_topic(push_constants.TOPIC_XLMM_A,
                                    {'target_url': target_url},
                                    description=message)

        mipush_of_android.push_to_topic(push_constants.TOPIC_XLMM_VIP,
                                        {'target_url': target_url},
                                        description=message)
        mipush_of_ios.push_to_topic(push_constants.TOPIC_XLMM_VIP,
                                    {'target_url': target_url},
                                    description=message)
