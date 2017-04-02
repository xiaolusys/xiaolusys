# coding: utf-8

from django.conf.urls import include, url
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page
from rest_framework.urlpatterns import format_suffix_patterns

from rest_framework import routers
from . import views


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'lackorder', views.LackGoodOrderViewSet)

router_urls = router.urls
router_urls += format_suffix_patterns([
    url(r'^purchasestats/$', views.PurchaseStatsApiView.as_view(), name='purchase-stats'),
])

urlpatterns = [
    url(r'^v1/', include(router_urls, namespace='dinghuo_v1')),
]