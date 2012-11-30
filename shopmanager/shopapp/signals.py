from django.dispatch import Signal

modify_fee_signal = Signal(providing_args=["user_id","trade_id"])
