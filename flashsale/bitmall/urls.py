# coding=utf-8
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from .views import BitMallView, BitMallRegisterView

urlpatterns = (
    url(r'^$', csrf_exempt(BitMallView.as_view())),
    url(r'^register/$', csrf_exempt(BitMallRegisterView.as_view())),
)
