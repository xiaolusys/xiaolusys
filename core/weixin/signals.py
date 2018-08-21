from django.dispatch import Signal

signal_weixin_snsauth_response = Signal(providing_args=['appid','resp_data'])