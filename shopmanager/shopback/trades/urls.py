from django.conf.urls.defaults import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from djangorestframework.views import InstanceModelView
from shopback.trades.views import StatisticMergeOrderView,CheckOrderView,OrderPlusView,ReviewOrderView,ExchangeOrderView,\
    OutStockOrderProductView,TradeSearchView,DirectOrderView,OrderListView,TradeLogisticView,change_trade_addr,change_trade_order,\
    delete_trade_order,change_logistic_and_outsid,review_order,update_sys_memo,change_order_stock_status,regular_trade,\
    ExchangeOrderInstanceView,DirectOrderInstanceView,replay_trade_send_result,countFenxiaoDetail
from shopback.base.renderers  import BaseJsonRenderer
from shopback.trades.renderers import CheckOrderRenderer,ReviewOrderRenderer,ExchangeOrderRender,DirectOrderRender,\
    StatisticMergeOrderRender,StatisticOutStockRender,OrderListRender,TradeLogisticRender
from shopback.trades.resources import TradeResource,OrderPlusResource,ExchangeOrderResource,MergeTradeResource,StatisticMergeOrderResource
from shopback.base.permissions import IsAuthenticated
from shopback.base.authentication import UserLoggedInAuthentication,login_required_ajax

urlpatterns = patterns('shopback.trades.views',
    
    (r'address/$',csrf_exempt(login_required_ajax(change_trade_addr))),
    (r'order/update/(?P<id>\d{1,20})/$',csrf_exempt(login_required_ajax(change_trade_order))),
    (r'order/delete/(?P<id>\d{1,20})/$',csrf_exempt(login_required_ajax(delete_trade_order))),
    (r'^order/outstock/(?P<id>\d{1,20})/$',csrf_exempt(login_required_ajax(change_order_stock_status))),
    (r'^replaysend/(?P<id>\d{1,20})/$',csrf_exempt(staff_member_required(replay_trade_send_result))),
    (r'review/(?P<id>\d{1,20})/$',csrf_exempt(login_required_ajax(review_order))),
    (r'logistic/$',csrf_exempt(login_required_ajax(change_logistic_and_outsid))),
    (r'^memo/$',csrf_exempt(login_required_ajax(update_sys_memo))), 
    (r'^regular/(?P<id>\d{1,20})/$',csrf_exempt(login_required_ajax(regular_trade))), 
    
    (r'^trade/(?P<id>\d{1,20})/$',InstanceModelView.as_view(
        resource=MergeTradeResource,
        #renderers=(BaseJsonRenderer,CheckOrderRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),                   
    (r'^checkorder/(?P<id>\d{1,20})/$',csrf_exempt(CheckOrderView.as_view(
        resource=TradeResource,
        renderers=(BaseJsonRenderer,CheckOrderRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    ))),
    (r'^orderplus/$',OrderPlusView.as_view(
        resource=OrderPlusResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    
    (r'^revieworder/(?P<id>\d{1,20})/$',staff_member_required(ReviewOrderView.as_view(
        resource=OrderPlusResource,
        renderers=(BaseJsonRenderer,ReviewOrderRenderer),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    ))),
    (r'^exchange/$',staff_member_required(ExchangeOrderView.as_view(
        resource=ExchangeOrderResource,
        renderers=(BaseJsonRenderer,ExchangeOrderRender),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    ))),
    url(r'^exchange/(?P<id>\d{1,20})/$',staff_member_required(ExchangeOrderInstanceView.as_view(
        resource=ExchangeOrderResource,
        renderers=(BaseJsonRenderer,ExchangeOrderRender),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),name="exchange_order_instance"),
    (r'^direct/$',staff_member_required(DirectOrderView.as_view(
        resource=ExchangeOrderResource,
        renderers=(BaseJsonRenderer,DirectOrderRender),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    ))),
   url (r'^direct/(?P<id>\d{1,20})/$',staff_member_required(DirectOrderInstanceView.as_view(
        resource=ExchangeOrderResource,
        renderers=(BaseJsonRenderer,DirectOrderRender),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),name="direct_order_instance"),
    (r'^tradeplus/$',TradeSearchView.as_view(
        resource=OrderPlusResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^order/statistic/$',StatisticMergeOrderView.as_view(
        resource=StatisticMergeOrderResource,
        renderers=(BaseJsonRenderer,StatisticMergeOrderRender),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^order/outstock/$',OutStockOrderProductView.as_view(
        resource=StatisticMergeOrderResource,
        renderers=(BaseJsonRenderer,StatisticOutStockRender),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    
    (r'^order/list/(?P<id>\d{1,20})/$',OrderListView.as_view(
        resource=OrderPlusResource,
        renderers=(BaseJsonRenderer,OrderListRender),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
        
    (r'^logistic/query/$',TradeLogisticView.as_view(
        resource=MergeTradeResource,
        renderers=(BaseJsonRenderer,TradeLogisticRender),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),               
    
    (r'fenxiao/count/$',csrf_exempt(countFenxiaoDetail)),
    
)