# coding: utf-8

from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page
from rest_framework.urlpatterns import format_suffix_patterns

from rest_framework import routers
from . import views_lackgood


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'lackorder', views_lackgood.LackGoodOrderViewSet)

router_urls = router.urls
router_urls += ([

])

urlpatterns = patterns('',
    url(r'^v1/', include(router_urls, namespace='dinghuo_v1')),
)