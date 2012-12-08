from django.conf.urls.defaults import patterns, include, url
from shopback.trades.views import change_trade_addr,CheckOrderView
from shopback.base.renderers  import BaseJsonRenderer
from shopback.trades.renderers import CheckOrderRenderer
from shopback.trades.resources import TradeResource
from shopback.base.permissions import IsAuthenticated
from shopback.base.authentication import UserLoggedInAuthentication

urlpatterns = patterns('',
                       
    (r'^checkorder/(?P<id>\d{1,20})/$',CheckOrderView.as_view(
        resource=TradeResource,
        renderers=(BaseJsonRenderer,CheckOrderRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'address/',change_trade_addr)
)