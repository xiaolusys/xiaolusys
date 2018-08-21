# coding=utf-8
"""
优惠券相关推送
"""
from flashsale.push.mipush import mipush_of_ios, mipush_of_android
from flashsale.protocol import get_target_url
from flashsale.protocol import constants as protocal_constants
from flashsale.push.models_message import PushMsgTpl


def user_coupon_release_push(customer_id, push_tpl_id=None, extra_content=None):
    """优惠券发放推送"""
    tpl = PushMsgTpl.objects.filter(id=push_tpl_id, is_valid=True).first()
    if not tpl:
        return
    tpl_content = tpl.tpl_content.format(extra_content) if extra_content else tpl.tpl_content
    msg = tpl.get_emoji_content(abs_content=tpl_content)
    if msg:
        target_url = get_target_url(protocal_constants.TARGET_TYPE_HOME_TAB_1)
        mipush_of_android.push_to_account(customer_id,
                                          {'target_url': target_url},
                                          description=msg)
        mipush_of_ios.push_to_account(customer_id,
                                      {'target_url': target_url},
                                      description=msg)

