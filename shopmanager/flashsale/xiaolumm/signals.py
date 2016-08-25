from django.dispatch import Signal

signal_push_pending_carry_to_cash = Signal(providing_args=['obj'])

signal_xiaolumama_register_success = Signal(providing_args=['xiaolumama', 'renew'])
