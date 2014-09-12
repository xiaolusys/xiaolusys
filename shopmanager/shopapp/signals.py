from django.dispatch import Signal
from shopback.signals import *

modify_fee_signal = Signal(providing_args=["user_id","trade_id"])
