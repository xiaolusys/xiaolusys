from django.dispatch import Signal

signal_push_pending_carry_to_cash = Signal(providing_args=['obj'])