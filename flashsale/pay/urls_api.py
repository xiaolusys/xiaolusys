# coding=utf-8
from django.conf.urls import include, url
from rest_framework import routers
from flashsale.pay.views import refund

router = routers.DefaultRouter(trailing_slash=False)

router.register(r'salerefund', refund.SaleRefundViewSet)


router_urls = router.urls
urlpatterns = [
    url(r'^v1/', include(router_urls, namespace='flashsale_pay_v1')),
]

