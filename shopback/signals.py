from django.dispatch import Signal

user_logged_in = Signal(providing_args=["user", "top_session", "top_parameters"])

merge_trade_signal = Signal(providing_args=['trade'])
order_refund_signal = Signal(providing_args=["obj"])

rule_signal = Signal(providing_args=["trade_id"])

change_addr_signal = Signal(providing_args=["tid"])
recalc_fee_signal = Signal(providing_args=["trade_id"])

confirm_trade_signal = Signal(providing_args=["trade_id"])

signal_product_upshelf = Signal(providing_args=["product_list"])

signal_product_downshelf = Signal(providing_args=["product_list"])
