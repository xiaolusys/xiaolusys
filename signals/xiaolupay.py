# coding:utf8
"""
参考: https://www.pingxx.com/api#event-事件类型
"""

from django.dispatch import Signal

signal_charge_success = Signal(providing_args=['data'])

signal_refund_success = Signal(providing_args=['data'])

signal_red_envelop_sent = Signal(providing_args=['data'])

signal_red_envelope_received = Signal(providing_args=['data'])