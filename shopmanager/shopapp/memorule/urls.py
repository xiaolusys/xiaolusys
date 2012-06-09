__author__ = 'meixqhi'
from django.conf.urls.defaults import patterns, include, url
from shopapp.memorule.views import UpdateTradeMemoView
from shopback.base.authentication import UserLoggedInAuthentication
from shopback.base.permissions import IsAuthenticated
from shopback.base.renderers import BaseJsonRenderer
from shopapp.memorule.resources import TradeRuleResource



urlpatterns = patterns('',

    url('memo/update/$',UpdateTradeMemoView.as_view(
        resource=TradeRuleResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    ),name='update_trade_memo'),

)