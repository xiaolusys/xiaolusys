# coding=utf-8
__author__ = 'meixqhi'

from django.conf.urls import include, url

from refund_analysis import RefundReason, refund_Invalid_Create
from .views_quality_tracert import tracert_Page_Show, tracert_Data_Collect
from viws_analysis import RefundRateView, RefundRecord

from shopback.refunds.views import *

urlpatterns = [
    url('update/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$', update_interval_refunds, name='interval_refund'),

    url(r'^product/add/$', staff_member_required(RefundProductView.as_view())),

    url('^product/del/(?P<id>\d{1,20})/$', delete_trade_order, name='refund_product_del'),

    url('^rel/$', relate_refund_product, name='relate_refund_product'),
    url('^refundproduct/change/$', refund_change, name='refund_change'),
    url('^exchange/(?P<seller_id>\d+)/(?P<tid>\w{1,32})/$', create_refund_exchange_trade, name='refund_exchange_create'),

    url(r'^refund/$', staff_member_required(RefundView.as_view())),
    url(r'^manager/$', staff_member_required(RefundManagerView.as_view())),


    # refund reason
    url('refund_analysis/$', staff_member_required(RefundReason.as_view()),
       name='refunde_reson_analysis'),

    # refund_Invalid_Create
    url('refund_invalid_create/$', staff_member_required(refund_Invalid_Create),
       name='refunde_reson_analysis'),

    # refund quality handler
    url('refund_quality_handler/$', staff_member_required(tracert_Page_Show),
       name='refunde_reson_analysis'),
    url('refund_quality_data/$', staff_member_required(tracert_Data_Collect),
       name='refunde_reson_analysis'),
    url('ref_rate/$', staff_member_required(RefundRateView.as_view()), ),
    url('ref_rcord/$', staff_member_required(RefundRecord.as_view()), )
]
