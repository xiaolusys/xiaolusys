# coding: utf8
from __future__ import absolute_import, unicode_literals
from django.conf import settings
"""
success response:
{
  "mch_id": "1236482102",
  "trade_type": "JSAPI",
  "result_code": "SUCCESS",
  "appid": "wx3f91056a2928ad2d",
  "prepay_id": "wx201611232246309bbafe03fc0104339812",
  "nonce_str": "EmLRq6BIKTd2a5wW",
  "return_code": "SUCCESS",
  "return_msg": "OK",
  "sign": "0545DF81CF1ADA8DE8287807794B9FCF"
}
fail response:
{
  'return_code': 'FAIL',
  'return_msg': 'appid and openid not match'
}
"""

class WXPayConf:
    """配置账号信息"""
    #=======【异步通知url设置】===================================
    #异步通知url，商户根据实际开发过程设定
    NOTIFY_URL = getattr(settings, 'WX_NOTIFY_URL', '')
    #=======【JSAPI路径设置】===================================
    #获取access_token过程中的跳转uri，通过跳转将code传入jsapi支付页面
    JS_API_CALL_URL = getattr(settings, 'WX_JS_API_CALL_URL', '')

    VERIFY_CERTIFICATE = True

    @staticmethod
    def wx_configs():
        return {
            'app_id': getattr(settings, 'WX_APPID', ''),
            'mch_id': getattr(settings, 'WX_MCHID', ''),
            'key': getattr(settings, 'WX_KEY', ''),
            'cert_pem_path': getattr(settings, 'WX_CERT_PEM_PATH', ''),
            'key_pem_path': getattr(settings, 'WX_KEY_PEM_PATH', ''),
            'refund_user_id': getattr(settings, 'WX_REFUND_USER_ID', '')
        }

    @staticmethod
    def pub_configs():
        return {
            'app_id': getattr(settings, 'WX_PUB_APPID', ''),
            'mch_id': getattr(settings, 'WX_PUB_MCHID', ''),
            'key': getattr(settings, 'WX_PUB_KEY', ''),
            'cert_pem_path': getattr(settings, 'WX_PUB_CERT_PEM_PATH', ''),
            'key_pem_path': getattr(settings, 'WX_PUB_KEY_PEM_PATH', ''),
            'refund_user_id': getattr(settings, 'WX_PUB_REFUND_USER_ID', '')
        }

    @staticmethod
    def we_configs():
        return {
            'app_id': getattr(settings, 'WEAPP_APPID', ''),
            'mch_id': getattr(settings, 'WEAPP_SECRET', ''),
            'key': getattr(settings, 'WEAPP_KEY', ''),
            'cert_pem_path': getattr(settings, 'WEAPP_CERT_PEM_PATH', ''),
            'key_pem_path': getattr(settings, 'WEAPP_KEY_PEM_PATH', ''),
            'refund_user_id': getattr(settings, 'WEAPP_REFUND_USER_ID', '')
        }


