from django.dispatch import Signal
from shopback.signals import *

modify_fee_signal = Signal(providing_args=["user_id","trade_id"])

weixin_referal_signal = Signal(providing_args=["user_openid","referal_from_openid"])

weixin_verifymobile_signal = Signal(providing_args=["user_openid"])

weixin_refund_signal = Signal(providing_args=["refund_id"])

weixin_readclick_signal = Signal(providing_args=["click_score_record_id"])

weixin_active_signal = Signal(providing_args=["active_id"])

weixin_surveyconfirm_signal = Signal(providing_args=["survey_id"])

weixin_sampleconfirm_signal = Signal(providing_args=["sample_order_id"])

minus_frozenscore_signal = Signal(providing_args=["forzen_score_id"])

signal_wxorder_pay_confirm = Signal(providing_args=['obj'])