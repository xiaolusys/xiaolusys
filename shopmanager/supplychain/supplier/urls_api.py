# coding: utf-8


from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page
from rest_framework.urlpatterns import format_suffix_patterns

from rest_framework import routers
from . import views


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'supplier', views.SaleSupplierViewSet)
router.register(r'saleproduct', views.SaleProductViewSet)
router.register(r'saleschedule', views.SaleScheduleViewSet)

router_urls = router.urls
router_urls += ([
    url(r'^saleschedule/(?P<schedule_id>[0-9]+)/product$',
        views.SaleScheduleDetailViewSet.as_view({'get': 'list'}),
        name='saleschedule-product-list'),
    url(r'^saleschedule/(?P<schedule_id>[0-9]+)/product$',
        views.SaleScheduleDetailViewSet.as_view({'post': 'create'}),
        name='saleschedule-product-create'),
    url(r'^saleschedule/(?P<schedule_id>[0-9]+)/product/(?P<pk>[0-9]+)$',
        views.SaleScheduleDetailViewSet.as_view({'get': 'retrieve'}),
        name='saleschedule-product-detail'),
])

urlpatterns = patterns('',
    url(r'^v1/', include(router_urls, namespace='apis_v1')),
)
