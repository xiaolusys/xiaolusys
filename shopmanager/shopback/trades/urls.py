from django.conf.urls.defaults import patterns, include, url
from shopback.trades.views import CheckOrderView,OrderPlusView,ReviewOrderView,change_trade_addr,\
    change_trade_order,delete_trade_order,change_logistic_and_outsid,review_order
from shopback.base.renderers  import BaseJsonRenderer
from django.views.decorators.csrf import csrf_exempt
from shopback.trades.renderers import CheckOrderRenderer,ReviewOrderRenderer
from shopback.trades.resources import TradeResource,OrderPlusResource
from shopback.base.permissions import IsAuthenticated
from shopback.base.authentication import UserLoggedInAuthentication,login_required_ajax

urlpatterns = patterns('',
                       
    (r'^checkorder/(?P<id>\d{1,20})/$',CheckOrderView.as_view(
        resource=TradeResource,
        renderers=(BaseJsonRenderer,CheckOrderRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^orderplus/$',OrderPlusView.as_view(
        resource=OrderPlusResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'address/',csrf_exempt(login_required_ajax(change_trade_addr))),
    (r'order/update/(?P<id>\d{1,20})/',csrf_exempt(login_required_ajax(change_trade_order))),
    (r'order/delete/(?P<id>\d{1,20})/',csrf_exempt(login_required_ajax(delete_trade_order))),
    
    (r'^revieworder/(?P<id>\d{1,20})/$',ReviewOrderView.as_view(
        resource=OrderPlusResource,
        renderers=(BaseJsonRenderer,ReviewOrderRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'review/(?P<id>\d{1,20})/',csrf_exempt(login_required_ajax(review_order))),
    (r'logistic/',csrf_exempt(login_required_ajax(change_logistic_and_outsid))),
)