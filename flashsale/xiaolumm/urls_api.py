# coding=utf-8
from django.conf.urls import include, url
from rest_framework import routers
from flashsale.xiaolumm.views import views_advertis

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'ninepic', views_advertis.NinePicAdverViewSet)

router_urls = router.urls
router_urls += ([])
urlpatterns = [
    url(r'^v1/', include(router_urls, namespace='xiaolumm-v1')),
]
