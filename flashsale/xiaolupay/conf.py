# coding: utf8
from __future__ import absolute_import, unicode_literals


WX = 'wx'
WEAPP = 'weapp'
ALIPAY = 'alipay'
WX_PUB = 'wx_pub'
ALIPAY_WAP = 'alipay_wap'
UPMP_WAP = 'upmp_wap'
SANDPAY  = 'sandpay'

CHANNEL_CHOICES = (
    (WX, u'微信APP支付'),
    (WEAPP, u'小程序支付'),
    (ALIPAY, u'支付宝APP支付'),
    (WX_PUB, u'公众号支付'),
    (ALIPAY_WAP, u'支付宝网页支付'),
    (UPMP_WAP, u'银联支付'),
    (SANDPAY,  u'杉德支付'),
)

DEFAULT_TRANSFER_CHANNEL = SANDPAY
