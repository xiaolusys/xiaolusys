# coding=utf-8
from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from rest_framework import routers

from shopback.warehouse.views import (PackageScanCheckView,
                                      PackageScanWeightView,
                                      PackagOrderExpressView,
                                      PackagOrderOperateView
                                      )

router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = patterns('shopback.warehouse.views',

                       (r'^scancheck/$', csrf_exempt(PackageScanCheckView.as_view())),
                       (r'^scanweight/$', csrf_exempt(PackageScanWeightView.as_view())),
                       (r'^express_order/$', csrf_exempt(PackagOrderExpressView.as_view())),
                       (r'^operate/$', csrf_exempt(PackagOrderOperateView.as_view())),
                       )
urlpatterns += router.urls
