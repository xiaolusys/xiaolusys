# coding=utf-8
from django.conf.urls import patterns, include, url

from rest_framework import routers
from . import views_api

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'user', views_api.UserViewSet)

router_urls = router.urls
urlpatterns = patterns('',
                       url(r'^v1/', include(router_urls, namespace='auth_v1')),
                       )
