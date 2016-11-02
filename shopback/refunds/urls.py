from django.conf.urls import patterns, include, url
# from djangorestframework.resources import ModelResource
from django.contrib.admin.views.decorators import staff_member_required
# from core.options.authentication import UserLoggedInAuthentication
# from core.options.permissions import IsAuthenticated
from shopback.refunds.views import RefundProductView, RefundView, RefundManagerView

# from core.options.renderers  import BaseJsonRenderer
# from shopback.refunds.renderers import RefundProductRenderer,RefundManagerRenderer
# from shopback.refunds.resources import RefundProductResource,RefundResource
from refund_analysis import RefundReason, refund_Invalid_Create
from .views_quality_tracert import tracert_Page_Show, tracert_Data_Collect
from viws_analysis import RefundRateView, RefundRecord

__author__ = 'meixqhi'

urlpatterns = patterns('shopback.refunds.views',

                       url('update/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$', 'update_interval_refunds',
                           name='interval_refund'),

                       (r'^product/add/$', staff_member_required(RefundProductView.as_view(
                           # resource=RefundProductResource,
                           # renderers=(BaseJsonRenderer,RefundProductRenderer),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       ))),

                       url('^product/del/(?P<id>\d{1,20})/$', 'delete_trade_order', name='refund_product_del'),

                       url('^rel/$', 'relate_refund_product', name='relate_refund_product'),
                        url('^refundproduct/change/$', 'refund_change', name='refund_change'),
                       url('^exchange/(?P<seller_id>\d+)/(?P<tid>\w{1,32})/$',
                           'create_refund_exchange_trade', name='refund_exchange_create'),

                       (r'^refund/$', staff_member_required(RefundView.as_view(
                           #         resource=RefundResource,
                           #         renderers=(BaseJsonRenderer,),
                           #         authentication=(UserLoggedInAuthentication,),
                           #         permissions=(IsAuthenticated,)
                       ))),

                       (r'^manager/$', staff_member_required(RefundManagerView.as_view(
                           # resource=RefundResource,
                           # renderers=(BaseJsonRenderer,RefundManagerRenderer),
                           # authentication=(UserLoggedInAuthentication,),
                           # permissions=(IsAuthenticated,)
                       ))),

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
                       )
