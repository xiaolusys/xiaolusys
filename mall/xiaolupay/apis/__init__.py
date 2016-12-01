# coding:utf8
from __future__ import absolute_import, unicode_literals
__ALL__ = ['Charge']

from django.conf import settings
import pingpp
pingpp.api_key = settings.PINGPP_APPKEY

ONLY_USE_XIAOLUPAY = getattr(settings, 'XIAOLU_UNIONPAY_SWITH', False)

if ONLY_USE_XIAOLUPAY:
    from .v1.charge import Charge
else:
    Charge = pingpp.Charge
    RedEnvelope = pingpp.RedEnvelope



