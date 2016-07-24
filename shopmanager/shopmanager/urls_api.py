# coding: utf-8

from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    url(r'^chain/', include('supplychain.supplier.urls_api')),
    url(r'^dinghuo/', include('flashsale.dinghuo.urls_api')),
    url(r'^forecast/', include('flashsale.forecast.urls')),
    url(r'^items/', include('shopback.items.urls_api')),
    url(r'^statistics/', include('statistics.urls_api')),
)
