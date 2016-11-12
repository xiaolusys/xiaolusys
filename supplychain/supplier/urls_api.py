# coding: utf-8

from django.conf.urls import include, url
from django.views.generic.base import TemplateView
from django.views.decorators.cache import cache_page
from rest_framework.urlpatterns import format_suffix_patterns

from rest_framework import routers
from . import views

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'supplier', views.SaleSupplierViewSet)
router.register(r'saleproduct', views.SaleProductViewSet)
router.register(r'saleschedule', views.SaleScheduleViewSet)
router.register(r'salescategory', views.SaleCategoryViewSet)
router.register(r'preferencepool', views.PreferencePoolViewSet)

router_urls = router.urls
router_urls += ([
    url(r'^saleschedule/(?P<schedule_id>[0-9]+)/product$',
        views.SaleScheduleDetailViewSet.as_view({'get': 'list'}),
        name='saleschedule-product-list'),
    url(r'^saleschedule/(?P<schedule_id>[0-9]+)/product/list_filters$',
        views.SaleScheduleDetailViewSet.as_view({'get': 'list_filters'}),
        name='saleschedule-product-list_filters'),
    url(r'^saleschedule/(?P<schedule_id>[0-9]+)/product$',
        views.SaleScheduleDetailViewSet.as_view({'post': 'create'}),
        name='saleschedule-product-create'),

    url(r'^saleschedule/(?P<schedule_id>[0-9]+)/product/(?P<pk>[0-9]+)$',
        views.SaleScheduleDetailViewSet.as_view({'delete': 'destroy'}),
        name='saleschedule-product-delete'),


    url(r'^saleschedule/(?P<schedule_id>[0-9]+)/product/(?P<pk>[0-9]+)$',
        views.SaleScheduleDetailViewSet.as_view({'get': 'retrieve'}),
        name='saleschedule-product-detail'),
    url(r'^saleschedule/(?P<schedule_id>[0-9]+)/create_manage_detail$',
        views.SaleScheduleDetailViewSet.as_view({'post': 'create_manage_detail'}),
        name='saleschedule-product-create_manage_detail'),
    url(r'^saleschedule/(?P<schedule_id>[0-9]+)/modify_manage_detail/(?P<pk>[0-9]+)$',
        views.SaleScheduleDetailViewSet.as_view({'patch': 'modify_manage_detail'}),
        name='saleschedule-product-modify-manage-detail'),

    url(r'^saleschedule/(?P<schedule_id>[0-9]+)/adjust_order_weight/(?P<pk>[0-9]+)$',
        views.SaleScheduleDetailViewSet.as_view({'patch': 'adjust_order_weight'}),
        name='saleschedule-product-adjust-order-weight'),

    url(r'^saleschedule/(?P<schedule_id>[0-9]+)/update_assign_worker$',
        views.SaleScheduleDetailViewSet.as_view({'post': 'update_assign_worker'}),
        name='saleschedule-product-update-assign-worker'),
])

urlpatterns = [
    url(r'^v1/', include(router_urls, namespace='chain_v1')),
]
