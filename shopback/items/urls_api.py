# coding: utf-8

from django.conf.urls import include, url

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
router_v2_urls += ([])


urlpatterns = [
    url(r'^v1/', include(router_urls, namespace='items_v1')),
    url(r'^v2/', include(router_v2_urls, namespace='items_v2')),
]

