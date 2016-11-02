from django.dispatch import Signal

signal_kefu_operate_record = Signal(providing_args=["kefu_id", "trade_id", "operation"])
