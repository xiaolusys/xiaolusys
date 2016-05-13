# coding=utf-8
__author__ = 'jie.lin'
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt
from statistics.views_pay import SaleNumberStatiticsView

urlpatterns = (
    url(r'^pay/salenum$', csrf_exempt(SaleNumberStatiticsView.as_view())),
)

