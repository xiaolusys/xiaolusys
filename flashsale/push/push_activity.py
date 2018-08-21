# coding=utf-8
"""
活动相关推送
"""
from flashsale.push.mipush import mipush_of_ios, mipush_of_android
from flashsale.protocol import get_target_url
from flashsale.protocol import constants as protocal_constants
from flashsale.push.models_message import PushMsgTpl


def activity_red_packet_release_push(customer_id):
    """ 活动红包发放推送 """
    msg = None
    tpls = PushMsgTpl.objects.filter(id=7, is_valid=True)
    if tpls.exists():
        tpl = tpls[0]
        msg = tpl.get_emoji_content()
    if msg:
        target_url = get_target_url(protocal_constants.TARGET_TYPE_HOME_TAB_1)
        mipush_of_android.push_to_account(customer_id,
                                          {'target_url': target_url},
                                          description=msg)
        mipush_of_ios.push_to_account(customer_id,
                                      {'target_url': target_url},
                                      description=msg)


def activity_open_red_packet_push(customer_id):
    """ 活动开红包推送 """
    msg = None
    tpls = PushMsgTpl.objects.filter(id=8, is_valid=True)
    if tpls.exists():
        tpl = tpls[0]
        msg = tpl.get_emoji_content()
    if msg:
        target_url = get_target_url(protocal_constants.TARGET_TYPE_HOME_TAB_1)
        mipush_of_android.push_to_account(customer_id,
                                          {'target_url': target_url},
                                          description=msg)
        mipush_of_ios.push_to_account(customer_id,
                                      {'target_url': target_url},
                                      description=msg)

