# coding=utf-8
__author__ = 'jie.lin'
from django.conf.urls import patterns, include, url
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from statistics.views_pay import SaleNumberStatiticsView
from rest_framework import routers
from statistics.views_stats import SaleStatsViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'salestats', SaleStatsViewSet)
router_urls = router.urls
router_urls += ([])

urlpatterns = (
    url(r'^pay/salenum$', csrf_exempt(staff_member_required(SaleNumberStatiticsView.as_view()))),
    url(r'^stats/', include(router_urls, namespace='stats')),
)

