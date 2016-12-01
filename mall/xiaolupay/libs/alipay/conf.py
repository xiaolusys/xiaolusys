# coding: utf8
from __future__ import absolute_import, unicode_literals

import os
from django.conf import settings

"""
success response:
{

}
fail response:
{
  "alipay_trade_create_response": {
    "msg": "Business Failed",
    "sub_code": "ACQ.INVALID_PARAMETER",
    "code": "40004",
    "sub_msg": "参数无效"
  },
  "sign": "hbXBtXHLaeYkqt4HP0gDaRqgiGsIR/T4N7cBGaBKrKrohkFV38/556oX408nA+eEwgftjWiYk7VjlzJcK6Obzfp/Ck3odiqZmF4pjYGZBNzdcRQqatw4qBDuU6/WgShajUHG4MWxfmpPN7cfMa2u6R9g2OxvucGCM8RhYKkDjaI="
}
"""

class AlipayConf:

    GATEWAY_URL = getattr(settings, 'ALIPAY_GATEWAY_URL', '')
    NOTIFY_URL = getattr(settings, 'ALIPAY_NOTIFY_URL', '')

    MCH_UID     = getattr(settings, 'ALIPAY_MCHID', '')
    APP_ID   = getattr(settings, 'ALIAPY_APPID', '')

    PRIVATE_KEY_PATH = getattr(settings, 'ALIPAY_RSA_PRIVATE_KEY_PATH', '')
    PUBLIC_KEY_PATH  = getattr(settings, 'ALIPAY_RSA_PUBLIC_KEY_PATH', '')

    VERIFY_CERTIFICATE = True
    STATUS_SUCCESS = 'TRADE_SUCCESS'
    AMOUNT_SETTER  = 100


