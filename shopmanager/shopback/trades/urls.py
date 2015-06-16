#coding=utf-8
from django.conf.urls.defaults import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from djangorestframework.views import InstanceModelView
from shopback.trades.views    import (StatisticMergeOrderView,
                                      CheckOrderView,
                                      OrderPlusView,
                                      ReviewOrderView,
                                      ExchangeOrderView,
                                      OutStockOrderProductView,
                                      TradeSearchView,
                                      DirectOrderView,
                                      OrderListView,
                                      TradeLogisticView,
                                      change_trade_addr,
                                      change_trade_order,
                                      delete_trade_order,
                                      change_logistic_and_outsid,
                                      review_order,
                                      update_sys_memo,
                                      change_order_stock_status,
                                      regular_trade,
                                      ExchangeOrderInstanceView,
                                      DirectOrderInstanceView,
                                      RelatedOrderStateView,
                                      ImprovePriorityView,
                                      replay_trade_send_result,
                                      countFenxiaoAcount,
                                      showFenxiaoDetail,
                                      PackageScanCheckView,
                                      PackageScanWeightView,
                                      
                                      )
from shopback.trades.views import detail,search_trade
from shopback.base.renderers  import BaseJsonRenderer
from shopback.trades.renderers import (CheckOrderRenderer,
                                       ReviewOrderRenderer,
                                       ExchangeOrderRender,
                                       DirectOrderRender,
                                       StatisticMergeOrderRender,
                                       StatisticOutStockRender,
                                       OrderListRender,
                                       TradeLogisticRender,
                                       RelatedOrderRenderer)
from shopback.trades.resources import (BaseResource,
                                       TradeResource,
                                       OrderPlusResource,
                                       ExchangeOrderResource,
                                       MergeTradeResource,
                                       StatisticMergeOrderResource)
from shopback.base.permissions import IsAuthenticated
from shopback.base.authentication import UserLoggedInAuthentication,login_required_ajax


from shopback.trades import views_product_analysis


urlpatterns = patterns('shopback.trades.views',
    
    (r'address/$',csrf_exempt(login_required_ajax(change_trade_addr))),
    (r'order/update/(?P<id>\d{1,20})/$',csrf_exempt(login_required_ajax(change_trade_order))),
    (r'order/delete/(?P<id>\d{1,20})/$',csrf_exempt(login_required_ajax(delete_trade_order))),
    (r'^order/outstock/(?P<id>\d{1,20})/$',csrf_exempt(login_required_ajax(change_order_stock_status))),
    (r'^replaysend/(?P<id>\d{1,20})/$',csrf_exempt(staff_member_required(replay_trade_send_result))),
    (r'review/(?P<id>\d{1,20})/$',csrf_exempt(login_required_ajax(review_order))),
    (r'logistic/$',csrf_exempt(login_required_ajax(change_logistic_and_outsid))),
    (r'^memo/$',csrf_exempt(login_required_ajax(update_sys_memo))), 
    (r'^priority/(?P<id>\d{1,20})/',ImprovePriorityView.as_view(
        resource=MergeTradeResource,
        renderers=(BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    (r'^regular/(?P<id>\d{1,20})/$',csrf_exempt(login_required_ajax(regular_trade))), 
    
    (r'^trade/(?P<id>\d{1,20})/$',InstanceModelView.as_view(
        resource=MergeTradeResource,
        renderers=(BaseJsonRenderer,CheckOrderRenderer),
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
    url(r'^exchange/(?P<id>\d{1,20})/$',
        staff_member_required(ExchangeOrderInstanceView.as_view(
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
   url(r'^direct/(?P<id>\d{1,20})/$',
        staff_member_required(DirectOrderInstanceView.as_view(
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
                       
    (r'^related/orders/$',RelatedOrderStateView.as_view(
        resource=BaseResource,
        renderers=(RelatedOrderRenderer,BaseJsonRenderer,),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
                       
    (r'^logistic/query/$',TradeLogisticView.as_view(
        resource=MergeTradeResource,
        renderers=(BaseJsonRenderer,TradeLogisticRender),
        authentication=(UserLoggedInAuthentication,),
        permissions=(IsAuthenticated,)
    )),
    
    (r'fenxiao/count/$',csrf_exempt(countFenxiaoAcount)),

    (r'fenxiao/count/detail/$',staff_member_required(showFenxiaoDetail)),
    
    (r'^scancheck/$',csrf_exempt(PackageScanCheckView.as_view(
        resource=BaseResource,
        renderers=(BaseJsonRenderer,),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    ))), 
     
    (r'^scanweight/$',csrf_exempt(PackageScanWeightView.as_view(
        resource=BaseResource,
        renderers=(BaseJsonRenderer,),
#        authentication=(UserLoggedInAuthentication,),
#        permissions=(IsAuthenticated,)
    ))), 
    (r'^detail/$',csrf_exempt(login_required_ajax(detail))),
    (r'^search_trade/$',csrf_exempt(login_required_ajax(search_trade))),


    # linjie add in here
    # 产品的销售件数，金额，退货率，次品率
    url(r'^product_analysis/$', views_product_analysis.product_Analysis, name="product_Analysis"),
    # 小鹿妈妈的订单情况
    url(r'^xlmm_product_analysis/$', views_product_analysis.xlmm_Product_Analysis, name="xlmm_Product_Analysis"),

)