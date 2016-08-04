# encoding=utf8
"""
推送商品给用户客户端
"""
from flashsale.push.mipush import mipush_of_ios, mipush_of_android
from flashsale.protocol import get_target_url
from flashsale.protocol import constants as protocal_constants
from flashsale.push.models_message import PushMsgTpl


def push_product_to_customer(customer_id, modelproduct):
    product_url = modelproduct.item_product.get_weburl()
    params = {'product_id': product_url}
    target_url = get_target_url(protocal_constants.TARGET_TYPE_PRODUCT, params=params)
    msg = None

    mstpl = PushMsgTpl.objects.filter(id=11, is_valid=True).first()
    if mstpl:
        msg = mstpl.get_emoji_content().format(modelproduct.name)

    if msg is not None:
        mipush_of_android.push_to_account(customer_id, {'target_url': target_url}, description=msg)
        mipush_of_ios.push_to_account(customer_id, {'target_url': target_url}, description=msg)
