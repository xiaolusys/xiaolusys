from django.dispatch import Signal

taobao_logged_in = Signal(providing_args=["user","top_session","top_appkey","top_parameters"])

  