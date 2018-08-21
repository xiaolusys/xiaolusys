# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.conf.urls import include, url
from rest_framework import routers

from .views import callback

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'callback', callback.FengchaoCallbackViewSet, 'callback')
router_urls = router.urls

urlpatterns = [
    url(r'^v1/', include(router_urls, namespace='honeycomb')),
]
