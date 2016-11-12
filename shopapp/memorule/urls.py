__author__ = 'meixqhi'
from django.conf.urls import include, url
from shopapp.memorule.views import (UpdateTradeMemoView,
                                    ProductRuleFieldsView,
                                    ComposeRuleByCsvFileView)

# from core.options.authentication import UserLoggedInAuthentication
# from core.options.permissions import IsAuthenticated
# from core.options.renderers import BaseJsonRenderer
# from shopapp.memorule.resources import TradeRuleResource



urlpatterns = [
    url('update/$', UpdateTradeMemoView.as_view(
       # resource=TradeRuleResource,
       # renderers=(BaseJsonRenderer,),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
    ), name='update_trade_memo'),

    url('rule/fields/$', ProductRuleFieldsView.as_view(
       # resource=TradeRuleResource,
       # renderers=(BaseJsonRenderer,),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
    ), name='rule_fields'),

    url(r'^composerule/import/$', ComposeRuleByCsvFileView.as_view(
       # resource=TradeRuleResource,
       # renderers=(BaseJsonRenderer,),
       # authentication=(UserLoggedInAuthentication,),
       # permissions=(IsAuthenticated,)
    )),
]
