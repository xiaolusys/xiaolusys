# coding=utf-8
from django.conf.urls import include, url
from rest_framework import routers
from flashsale.protocol import views

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'apppushmsg', views.APPFullPushMessgeViewSet)

router_urls = router.urls
router_urls += ([])
urlpatterns = [
    url(r'^v1/', include(router_urls, namespace='protocol-v1')),
]
