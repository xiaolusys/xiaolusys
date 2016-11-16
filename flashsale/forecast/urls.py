# coding=utf-8
from django.conf.urls import include, url
from rest_framework import routers, viewsets

from .views import StagingInboundViewSet, ForecastManageViewSet, InBoundViewSet, ForecastStatsViewSet


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'staging', StagingInboundViewSet)
router.register(r'manage', ForecastManageViewSet)
router.register(r'inbound', InBoundViewSet)
router.register(r'stats', ForecastStatsViewSet)


router_urls = router.urls

router_urls += ([])

urlpatterns = [
     url(r'^v1/', include(router_urls, namespace='forecast_v1')),
     # url(r'^dashboard', staff_member_required(PurchaseDashBoardAPIView.as_view()), name="forecast_dashboard"),
]

