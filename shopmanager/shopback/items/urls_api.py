# coding: utf-8

from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page
from rest_framework.urlpatterns import format_suffix_patterns

from rest_framework import routers
from . import views


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'product', views.ProductManageViewSet)

router_urls = router.urls
router_urls += ([

])

router_v2 = routers.DefaultRouter(trailing_slash=False)
router_v2.register(r'product', views.ProductManageV2ViewSet)
router_v2_urls = router_v2.urls
router_v2_urls += ([
                       url(r'^product/(?P<pk>[0-9]+)/update_sku$',
                           views.ProductManageV2ViewSet.as_view({'post': 'update_sku'}),
                           name='model-product-update-sku'),
                   ])

urlpatterns = patterns('',
                       url(r'^v1/', include(router_urls, namespace='items_v1')),
                       url(r'^v2/', include(router_v2_urls, namespace='items_v2')),
                       )