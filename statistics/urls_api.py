# coding=utf-8
from django.conf.urls import include, url
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework import routers
from .views import views_apis


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'stats', views_apis.SaleStatsViewSet)

v1_router_urls = router.urls
v1_router_urls += ([])

urlpatterns = [
    url(r'^v1/', include(v1_router_urls, namespace='statistic_v1')),
]
