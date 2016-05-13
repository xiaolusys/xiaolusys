# coding=utf-8
__author__ = 'jie.lin'
from django.conf.urls import url
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from statistics.views_pay import SaleNumberStatiticsView

urlpatterns = (
    url(r'^pay/salenum$', csrf_exempt(staff_member_required(SaleNumberStatiticsView.as_view()))),
)

