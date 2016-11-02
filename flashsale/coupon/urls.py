# coding=utf-8
__author__ = 'jie.lin'
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from flashsale.coupon.views import RefundCouponView, ReleaseOmissive

urlpatterns = (
    url(r'^rsrc/$', csrf_exempt(RefundCouponView.as_view())),
    url(r'^release_coupon/$', csrf_exempt(ReleaseOmissive.as_view())),
)
