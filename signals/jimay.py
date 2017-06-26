# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.dispatch import Signal

# 己美医学代理注册成功
signal_jimay_agent_enrolled = Signal(providing_args=['obj', 'time_enrolled'])

# 己美医学代理订单付款成功
signal_jimay_agent_order_paid = Signal(providing_args=['obj', 'time_paid'])