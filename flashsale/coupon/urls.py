# coding=utf-8
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from flashsale.coupon.views import ReleaseOmissive, VerifyReturnSysTransfer

urlpatterns = (
    url(r'^release_coupon/$', csrf_exempt(ReleaseOmissive.as_view())),
    url(r'^verify_return_transfer/$', csrf_exempt(VerifyReturnSysTransfer.as_view())),
)
