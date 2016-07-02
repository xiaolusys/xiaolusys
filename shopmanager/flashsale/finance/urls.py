# coding: utf-8

from django.conf.urls import include, url
from rest_framework import routers, viewsets
from flashsale.finance.views import BillViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'bill_list', BillViewSet,'bill_list')


urlpatterns = [
    # url(r'^bill/(?P<bill_id>[0-9]+)/$', 'flashsale.finance.views.bill_detail', name='bill_detail'),
    # url(r'^confirm_bill/$', 'flashsale.finance.views.confirm_bill', name='confirm_bill'),
    # url(r'^deal/$', 'flashsale.finance.views.deal', name='deal'),
    # url(r'^pay_bill/$', 'flashsale.finance.views.pay_bill', name='pay_bill'),
    # url(r'^change_note/$', 'flashsale.finance.views.change_note', name='change_note'),
    # url(r'^finish_bill/$', 'flashsale.finance.views.finish_bill', name='finish_bill')
]

urlpatterns += router.urls
