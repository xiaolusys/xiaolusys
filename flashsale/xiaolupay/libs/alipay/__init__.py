# coding: utf8
from __future__ import absolute_import, unicode_literals

__ALL__ = ['AliPay', 'AlipayConf', 'AliPayException']
from .app import AliPay
from .conf import AlipayConf
from .exceptions import AliPayException

# def includeme(config):
#     settings = config.registry.settings
#     config.registry['alipay'] = Alipay(
#         pid=settings.get('alipay.pid'),
#         key=settings.get('alipay.key'),
#         seller_email=settings.get('alipay.seller_email')
#     )

