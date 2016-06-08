# coding: utf-8

from django.conf.urls import include, url


urlpatterns = (
    url(r'^bill/(?P<bill_id>[0-9]+)/$', 'flashsale.finance.views.bill_detail', name='bill_detail'),
    url(r'^confirm_bill/$', 'flashsale.finance.views.confirm_bill', name='confirm_bill'),
    url(r'^deal/$', 'flashsale.finance.views.deal', name='deal')
)
