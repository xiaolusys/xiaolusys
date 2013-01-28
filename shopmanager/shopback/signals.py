from django.dispatch import Signal

taobao_logged_in = Signal(providing_args=["user","top_session","top_parameters"])

merge_trade_signal = Signal(providing_args=["tid"])
refund_signal      = Signal(providing_args=["refund"])

rule_signal = Signal(providing_args=["trade_id"])

