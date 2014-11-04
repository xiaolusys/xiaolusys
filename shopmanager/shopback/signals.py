from django.dispatch import Signal

user_logged_in = Signal(providing_args=["user","top_session","top_parameters"])

merge_trade_signal = Signal(providing_args=['trade'])
refund_signal      = Signal(providing_args=["refund"])

rule_signal        = Signal(providing_args=["trade_id"])

change_addr_signal = Signal(providing_args=["tid"])
recalc_fee_signal  = Signal(providing_args=["trade_id"])

confirm_trade_signal = Signal(providing_args=["trade_id"])


