# coding: utf-8
from __future__ import unicode_literals

from django.conf.urls import include, url

urlpatterns = [
    url(r'^chain/', include('pms.supplier.urls_api')),
    url(r'^dinghuo/', include('shopback.dinghuo.urls_api')),
    url(r'^forecast/', include('shopback.forecast.urls')),
    url(r'^items/', include('shopback.items.urls_api')),
    url(r'^statistics/', include('statistics.urls_api')),
    url(r'^auth/', include('shopback.users.urls_api')),
    url(r'^finance/', include('flashsale.finance.urls')),
    url(r'^pay/', include('flashsale.pay.urls')),
    url(r'^xiaolumm/', include('flashsale.xiaolumm.urls')),
    url(r'^protocol/', include('flashsale.protocol.urls')),
    url(r'^daystats/', include('statistics.daystats.urls_api')),
]
