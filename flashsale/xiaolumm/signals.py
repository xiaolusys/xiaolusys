# encoding=utf8
from django.dispatch import Signal

signal_push_pending_carry_to_cash = Signal(providing_args=['obj'])

signal_xiaolumama_register_success = Signal(providing_args=['xiaolumama', 'renew'])

# 产生点击收益
clickcarry_signal = Signal(providing_args=[])
