from django.conf.urls.defaults import patterns, include, url
from djangorestframework.resources import ModelResource
from django.contrib.admin.views.decorators import staff_member_required
from shopback.base.authentication import UserLoggedInAuthentication
from shopback.base.permissions import IsAuthenticated
from shopback.refunds.views import RefundProductView,RefundView,RefundManagerView
from shopback.base.renderers  import BaseJsonRenderer
from shopback.refunds.renderers import RefundProductRenderer,RefundManagerRenderer
from shopback.refunds.resources import RefundProductResource,RefundResource

__author__ = 'meixqhi'

urlpatterns = patterns('shopback.refunds.views',

    url('update/(?P<dt_f>[^/]+)/(?P<dt_t>[^/]+)/$','update_interval_refunds',name='interval_refund'),
    
    (r'^product/add/$',staff_member_required(RefundProductView.as_view(
        resource=RefundProductResource,
        renderers=(BaseJsonRenderer,RefundProductRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    ))),
                       
    url('^product/del/(?P<id>\d{1,20})/$','delete_trade_order',name='refund_product_del'),  
    
    url('^rel/$','relate_refund_product',name='relate_refund_product'),  
                     
    url('^exchange/(?P<seller_id>[0-9]{11}/(?P<tid>\w{1,32})/$',
         'create_refund_exchange_trade',name='refund_exchange_create'), 
                     
    (r'^refund/$',staff_member_required(RefundView.as_view(
        resource=RefundResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    ))),
    
    (r'^manager/$',staff_member_required(RefundManagerView.as_view(
        resource=RefundResource,
        renderers=(BaseJsonRenderer,RefundManagerRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    ))),
)
