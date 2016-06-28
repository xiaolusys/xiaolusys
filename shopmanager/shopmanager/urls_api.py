# coding: utf-8

from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
    url(r'^purchase/', include('supplychain.supplier.urls_api')),
)
