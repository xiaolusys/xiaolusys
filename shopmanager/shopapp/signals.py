from django.dispatch import Signal
from shopback.signals import *

modify_fee_signal = Signal(providing_args=["user_id","trade_id"])

weixin_referal_signal = Signal(providing_args=["user_openid","referal_from_openid"])

weixin_refund_signal = Signal(providing_args=["refund_id"])

weixin_readclick_signal = Signal(providing_args=["click_score_record_id"])
