# coding=utf-8
from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from rest_framework import routers

from shopback.warehouse.views import (PackageScanCheckView,
                                      PackageScanWeightView,
                                      PackagOrderExpressView,
                                      PackagOrderOperateView,
                                      PackagOrderRevertView,
                                      package_order_print_pickle
                                      )

router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = patterns('shopback.warehouse.views',

                       (r'^scancheck/$', csrf_exempt(PackageScanCheckView.as_view())),
                       (r'^scanweight/$', csrf_exempt(PackageScanWeightView.as_view())),
                       (r'^express_order/$', csrf_exempt(PackagOrderExpressView.as_view())),
                       (r'^operate/$', csrf_exempt(PackagOrderOperateView.as_view())),
                       (r'^revert/$', csrf_exempt(PackagOrderRevertView.as_view())),
                       (r'^print_pickle/$', package_order_print_pickle),
                       )
urlpatterns += router.urls
