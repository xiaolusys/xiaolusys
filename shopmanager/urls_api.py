# coding: utf-8
from django.conf.urls import include, url

urlpatterns = [
    url(r'^chain/', include('supplychain.supplier.urls_api')),
    url(r'^dinghuo/', include('flashsale.dinghuo.urls_api')),
    url(r'^forecast/', include('flashsale.forecast.urls')),
    url(r'^items/', include('shopback.items.urls_api')),
    url(r'^statistics/', include('statistics.urls_api')),
    url(r'^auth/', include('shopback.users.urls_api')),
    url(r'^finance/', include('flashsale.finance.urls_api')),
    url(r'^pay/', include('flashsale.pay.urls_api')),
    url(r'^xiaolumm/', include('flashsale.xiaolumm.urls_api')),
    url(r'^protocol/', include('flashsale.protocol.urls_api')),
]
