# coding=utf-8
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page

from .views import BitMallView, BitMallRegisterView, BitMallRegStatusView

urlpatterns = (
    url(r'^$', csrf_exempt(BitMallView.as_view())),
    url(r'^register/$', csrf_exempt(BitMallRegisterView.as_view())),
    url(r'^register/success/$', csrf_exempt(BitMallRegStatusView.as_view())),
    url(r'^register/pay.htm$', cache_page(24 * 60 * 60)(TemplateView.as_view(template_name="pay/pay.html"))),
)
