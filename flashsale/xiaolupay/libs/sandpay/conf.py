# coding: utf8
from __future__ import absolute_import, unicode_literals

import random
from django.conf import settings


class SandpayConf:

    SANDPAY_API_GETWAY      = getattr(settings, 'SANDPAY_API_GETWAY', '')
    SANDPAY_RSA_CERT_PATH   = getattr(settings, 'SANDPAY_RSA_CERT_PATH', '')
    SANDPAY_RSA_KEY_PATH    = getattr(settings, 'SANDPAY_RSA_KEY_PATH', '')
    SANDPAY_AGENT_PAY_NOTICE_URL = getattr(settings, 'SANDPAY_AGENT_PAY_NOTICE_URL', '')

    AC_MERCHANT = '0'
    AC_PLATFORM = '1'

    ACC_ATTR_PUB = '1'
    ACC_ATTR_PRI = '0'

    ACC_TYPE_COMP = '3'
    ACC_TYPE_BANK = '4'

    DEFAULT_CURRENCY_CODE = '156' #cny

    RFLAG_SUCCESS = '0'
    RFLAG_FAIL    = '1'
    RFLAG_PENDING = '2'

    PRO_RECEV2PUB = ('00000001', ACC_ATTR_PUB)
    PRO_RECEV2PRI = ('00000002', ACC_ATTR_PRI)
    PRO_TRANS2PUB = ('00000003', ACC_ATTR_PUB)
    PRO_TRANS2PRI = ('00000004', ACC_ATTR_PRI)

    @classmethod
    def gen_aes_secret(cls):
        return ''.join(random.sample('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', 16))